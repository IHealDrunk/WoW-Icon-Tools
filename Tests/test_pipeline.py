import sys
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Scripts'))
from utils import BuildState, BuildControl, SaveAndExit, sha256, atomic_write, path_key
import blp_to_png as convert
import resize_png as resize


class PipelineTests(unittest.TestCase):
    def test_recovery_modification_review_and_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blp, png, resized, review = [root / n for n in ('BLP', 'PNG', 'Resized', 'Review')]
            source = blp / 'Nested' / 'Icon.BLP'
            source.parent.mkdir(parents=True)
            def fixture(color, size=(64, 64)):
                Image.new('RGB', size, color).convert('P').save(source, 'BLP')
            fixture('red')
            state = BuildState(root / 'state.json')
            with patch.multiple(convert, BLP_FOLDER=blp, PNG_FOLDER=png), patch.multiple(
                    resize, PNG_FOLDER=png, RESIZED_FOLDER=resized, REVIEW_FOLDER=review):
                ready = convert.convert_blp_to_png(state)
                outputs = resize.resize_icons(state, png_files=ready)
                self.assertEqual(len(outputs), 1)
                output = outputs[0]
                first = sha256(output)
                stamp = output.stat().st_mtime_ns
                recovered = BuildState(state.path)
                resize.resize_icons(recovered, png_files=convert.convert_blp_to_png(recovered))
                self.assertEqual(stamp, output.stat().st_mtime_ns)
                fixture('blue')
                resize.resize_icons(recovered, png_files=convert.convert_blp_to_png(recovered))
                self.assertNotEqual(first, sha256(output))
                output.write_bytes(b'broken')
                resize.resize_icons(recovered, png_files=convert.convert_blp_to_png(recovered))
                with Image.open(output) as image:
                    self.assertEqual(image.size, (128, 128))
                fixture('green', (32, 32))
                self.assertEqual(resize.resize_icons(recovered, png_files=convert.convert_blp_to_png(recovered)), [])
                self.assertFalse(output.exists())
                self.assertTrue((review / 'Nested' / 'Icon.png').exists())
                source.write_bytes(b'not a BLP')
                self.assertEqual(convert.convert_blp_to_png(recovered), [])

    def test_atomic_failure_and_pause(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'out.png'
            path.write_bytes(b'original')
            def fail(temporary):
                temporary.write_bytes(b'partial')
                raise RuntimeError('failure')
            with self.assertRaises(RuntimeError):
                atomic_write(path, fail)
            self.assertEqual(path.read_bytes(), b'original')
            state = BuildState(Path(directory) / 'state.json')
            BuildControl(state, reader=lambda _: 'r').pause()
            with self.assertRaises(SaveAndExit):
                BuildControl(state, reader=lambda _: 's').pause()
            self.assertEqual(BuildState(state.path).data['status'], 'saved')
            self.assertEqual(path_key(Path('Folder/Icon.BLP')), path_key(Path('folder/icon.blp')))

    def test_render_fingerprints_and_atomic_export(self):
        import gimp_render
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'input.png'
            output = root / 'nested' / 'output.tga'
            Image.new('RGBA', (128, 128), 'red').save(source)
            settings = {'export_format': '.tga'}
            def fake_render(settings, source, destination):
                Image.open(source).save(destination, 'TGA')
                return True
            with patch.object(gimp_render, '_render_icon', side_effect=fake_render):
                self.assertTrue(gimp_render.render_icon(settings, source, output))
            state = BuildState(root / 'state.json')
            state.complete('render', Path('Nested/Icon.png'), 'source-template', output)
            recovered = BuildState(state.path)
            self.assertTrue(recovered.current('render', Path('nested/icon.PNG'), 'source-template', output))
            self.assertFalse(recovered.current('render', Path('nested/icon.png'), 'changed-template', output))
            original = output.read_bytes()
            with patch.object(gimp_render, '_render_icon', side_effect=RuntimeError('GIMP failed')):
                with self.assertRaises(RuntimeError):
                    gimp_render.render_icon(settings, source, output)
            self.assertEqual(original, output.read_bytes())
            output.unlink()
            self.assertFalse(recovered.current('render', Path('nested/icon.png'), 'source-template', output))

    def test_raw_bgra_pixels_bounds_and_resume(self):
        from blp_to_png import load_blp, InvalidBLP
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blp = root / 'BLP'
            blp.mkdir()
            source = blp / 'Raw.BLP'
            # Two pixels with distinct channel values and non-opaque alpha.
            pixels = bytes([3, 2, 1, 127, 30, 20, 10, 255])
            def raw(alpha=8, offset=148, length=8, width=2, height=1):
                header = bytearray(148)
                struct.pack_into('<4sIBBBBII', header, 0, b'BLP2', 1, 3, alpha, 8, 0, width, height)
                struct.pack_into('<I', header, 20, offset)
                struct.pack_into('<I', header, 84, length)
                return bytes(header) + pixels
            source.write_bytes(raw())
            with load_blp(source) as image:
                self.assertEqual(image.getpixel((0, 0)), (1, 2, 3, 127))
                self.assertEqual(image.getpixel((1, 0)), (10, 20, 30, 255))
            source.write_bytes(raw(alpha=0))
            with load_blp(source) as image:
                self.assertEqual(image.getpixel((0, 0)), (1, 2, 3, 255))
            state = BuildState(root / 'state.json')
            with patch.multiple(convert, BLP_FOLDER=blp, PNG_FOLDER=root / 'PNG'):
                ready = convert.convert_blp_to_png(state)
                self.assertEqual(len(ready), 1)
                stamp = ready[0].stat().st_mtime_ns
                with patch.object(convert, 'load_blp', side_effect=AssertionError('must skip')):
                    self.assertEqual(convert.convert_blp_to_png(BuildState(state.path)), ready)
                self.assertEqual(ready[0].stat().st_mtime_ns, stamp)
            for broken in (raw(offset=10), raw(length=9), raw(width=0),
                           raw(width=100000, height=100000), raw()[:-1], bytes(148)):
                source.write_bytes(broken)
                with self.assertRaises(InvalidBLP):
                    load_blp(source)

    def test_failed_hash_cache_good_skips_and_retry_on_change(self):
        import io
        from contextlib import redirect_stdout
        from blp_to_png import load_blp
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blp = root / 'BLP'
            blp.mkdir()
            bad = blp / 'Bad.blp'
            good = blp / 'Good.blp'
            bad.write_bytes(bytes(148))
            Image.new('RGB', (64, 64), 'red').convert('P').save(good, 'BLP')
            state = BuildState(root / 'state.json')
            capture = io.StringIO()
            with patch.multiple(convert, BLP_FOLDER=blp, PNG_FOLDER=root / 'PNG'), redirect_stdout(capture):
                ready = convert.convert_blp_to_png(state)
                self.assertEqual(len(ready), 1)
                stamp = ready[0].stat().st_mtime_ns
                recovered = BuildState(state.path)
                self.assertTrue(recovered.failure('convert', Path('BAD.BLP'), sha256(bad)))
                with patch.object(convert, 'load_blp', side_effect=AssertionError('must not decode unchanged files')):
                    self.assertEqual(convert.convert_blp_to_png(recovered), ready)
                self.assertEqual(stamp, ready[0].stat().st_mtime_ns)
                Image.new('RGB', (64, 64), 'blue').convert('P').save(bad, 'BLP')
                with patch.object(convert, 'load_blp', wraps=load_blp) as decoder:
                    ready = convert.convert_blp_to_png(BuildState(state.path))
                    self.assertEqual(len(ready), 2)
                    self.assertEqual(decoder.call_count, 1)
                self.assertIsNone(BuildState(state.path).failure('convert', Path('bad.blp'), sha256(bad)))
                # A damaged PNG must be rebuilt even when the good BLP is unchanged.
                (root / 'PNG' / 'Good.png').write_bytes(b'damaged')
                with patch.object(convert, 'load_blp', wraps=load_blp) as decoder:
                    self.assertEqual(len(convert.convert_blp_to_png(BuildState(state.path))), 2)
                    self.assertEqual(decoder.call_count, 1)
            self.assertIn('Left: 0', capture.getvalue())
            self.assertIn('Unchanged bad BLPs skipped: 1', capture.getvalue())
            self.assertIn('Reused PNGs: 1', capture.getvalue())

    def test_legacy_good_png_is_verified_without_rewriting(self):
        from blp_to_png import load_blp
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blp = root / 'BLP'
            png = root / 'PNG'
            blp.mkdir(); png.mkdir()
            source = blp / 'Legacy.blp'
            output = png / 'Legacy.png'
            Image.new('RGB', (64, 64), 'red').convert('P').save(source, 'BLP')
            with load_blp(source) as image:
                image.save(output, 'PNG')
            stamp = output.stat().st_mtime_ns
            state = BuildState(root / 'state.json')
            with patch.multiple(convert, BLP_FOLDER=blp, PNG_FOLDER=png):
                with patch.object(convert, 'atomic_write', side_effect=AssertionError('good legacy PNG must not be rewritten')):
                    self.assertEqual(convert.convert_blp_to_png(state), [output])
                self.assertEqual(stamp, output.stat().st_mtime_ns)
                with patch.object(convert, 'load_blp', side_effect=AssertionError('must reuse established record')):
                    self.assertEqual(convert.convert_blp_to_png(BuildState(state.path)), [output])
                # An unrelated legacy PNG cannot be adopted.
                Image.new('RGBA', (64, 64), 'blue').save(output, 'PNG')
                state = BuildState(root / 'new-state.json')
                self.assertEqual(convert.convert_blp_to_png(state), [output])
                with Image.open(output) as image:
                    self.assertEqual(image.getpixel((0, 0))[:3], (255, 0, 0))

    def test_resize_skips_image_work_and_legacy_output(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png, resized, review = [root / name for name in ('PNG', 'Resized', 'Review')]
            png.mkdir()
            source = png / 'Icon.png'
            Image.new('RGBA', (64, 64), 'red').save(source)
            state = BuildState(root / 'state.json')
            capture = io.StringIO()
            with patch.multiple(resize, PNG_FOLDER=png, RESIZED_FOLDER=resized, REVIEW_FOLDER=review), redirect_stdout(capture):
                ready = resize.resize_icons(state)
                stamp = ready[0].stat().st_mtime_ns
                with patch.object(resize.Image, 'open', side_effect=AssertionError('skip all image work')):
                    self.assertEqual(resize.resize_icons(BuildState(state.path)), ready)
                self.assertEqual(stamp, ready[0].stat().st_mtime_ns)
                # Matching legacy resized output is reused without rewriting.
                with patch.object(resize, 'atomic_write', side_effect=AssertionError('do not rewrite')):
                    self.assertEqual(resize.resize_icons(BuildState(root / 'legacy.json')), ready)
                Image.new('RGBA', (32, 32), 'blue').save(source)
                self.assertEqual(resize.resize_icons(state), [])
                with patch.object(resize.Image, 'open', side_effect=AssertionError('skip review image work')):
                    self.assertEqual(resize.resize_icons(BuildState(state.path)), [])
            self.assertIn('Left: 0', capture.getvalue())
            self.assertIn('Reused: 1', capture.getvalue())
            self.assertIn('Review: 1', capture.getvalue())

    def test_template_rotation_adoption_changes_and_migration(self):
        import io
        from contextlib import redirect_stdout
        import build_icon
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resized, icons = root / 'Resized', root / 'Icons'
            source = resized / 'Nested' / 'Icon.png'
            source.parent.mkdir(parents=True)
            output = icons / 'Nested' / 'Icon.tga'
            output.parent.mkdir(parents=True)
            Image.new('RGBA', (128, 128), 'red').save(source)
            Image.new('RGBA', (128, 128), 'red').save(output, 'TGA')
            onyx_bytes = output.read_bytes()
            settings = {'export_format': '.tga', 'folder_name': 'Onyx'}
            state = BuildState(root / 'state.json')
            def fake_batch(settings, jobs, callback, control=None):
                for source, output in jobs:
                    with Image.open(source) as image:
                        image.save(output, 'TGA')
                    callback(source, output, None)
            with patch.multiple(build_icon, RESIZED_FOLDER=resized, ICONS_FOLDER=icons), redirect_stdout(io.StringIO()):
                with patch.object(build_icon, 'render_batch', side_effect=AssertionError('adoption must bypass GIMP')):
                    stamp = output.stat().st_mtime_ns
                    self.assertEqual(build_icon.render_icons(settings, [source], state, BuildControl(state), 'onyx-v1', True), (0, 1, 0))
                    self.assertEqual(stamp, output.stat().st_mtime_ns)
                Image.new('RGBA', (128, 128), 'blue').save(output, 'TGA')
                eclipse_bytes = output.read_bytes()
                eclipse = {'export_format': '.tga', 'folder_name': 'Eclipse'}
                with patch.object(build_icon, 'render_batch', side_effect=AssertionError('adoption must bypass GIMP')):
                    self.assertEqual(build_icon.render_icons(eclipse, [source], state, BuildControl(state), 'eclipse-v1', True), (0, 1, 0))
                recovered = BuildState(state.path)
                self.assertEqual(set(recovered.data['templates']), {'onyx', 'eclipse'})
                output.write_bytes(onyx_bytes)
                with patch.object(build_icon, 'render_batch', side_effect=AssertionError('unchanged file must skip GIMP')):
                    # Editing the template updates only new/modified sources.
                    self.assertEqual(build_icon.render_icons(settings, [source], recovered, BuildControl(recovered), 'onyx-v2'), (0, 1, 0))
                # Changed sources are rebuilt, even when adoption was selected.
                Image.new('RGBA', (128, 128), 'green').save(source)
                with patch.object(build_icon, 'render_batch', side_effect=fake_batch) as batch:
                    self.assertEqual(build_icon.render_icons(settings, [source], recovered, BuildControl(recovered), 'onyx-v2', True), (1, 0, 0))
                    self.assertEqual(batch.call_count, 1)
                output.write_bytes(b'broken')
                with patch.object(build_icon, 'render_batch', side_effect=fake_batch):
                    self.assertEqual(build_icon.render_icons(settings, [source], recovered, BuildControl(recovered), 'onyx-v2'), (1, 0, 0))
                output.unlink()
                with patch.object(build_icon, 'render_batch', side_effect=fake_batch):
                    self.assertEqual(build_icon.render_icons(settings, [source], recovered, BuildControl(recovered), 'onyx-v2'), (1, 0, 0))
                legacy = BuildState(root / 'legacy.json')
                relative = source.relative_to(resized)
                legacy.complete('render', relative, sha256(source) + 'onyx-v1', output)
                legacy.migrate_render_history('Onyx', 'onyx-v1')
                self.assertTrue(legacy.render_current('ONYX', relative, sha256(source), output))
                self.assertFalse(legacy.render_current('Eclipse', relative, sha256(source), output))
                self.assertNotIn('render:' + path_key(relative), legacy.data['stages'])

    def test_native_128_support_and_old_review_migration(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png, resized, review = [root / n for n in ('PNG', 'Resized', 'Review')]
            png.mkdir(); review.mkdir()
            source = png / 'Native.png'
            image = Image.new('RGBA', (128, 128), (1, 2, 3, 127))
            image.putpixel((0, 0), (255, 10, 20, 0))
            image.save(source)
            review_file = review / source.name
            image.save(review_file)
            state = BuildState(root / 'state.json')
            # v1.3 initially routed 128x128 images to review, without a policy tag.
            state.complete('review', Path(source.name), sha256(source) + ':resize-v1', review_file)
            with patch.multiple(resize, PNG_FOLDER=png, RESIZED_FOLDER=resized, REVIEW_FOLDER=review), redirect_stdout(io.StringIO()):
                ready = resize.resize_icons(state)
                self.assertEqual(len(ready), 1)
                with Image.open(ready[0]) as actual:
                    self.assertEqual(actual.size, (128, 128))
                    self.assertEqual(actual.tobytes(), image.tobytes())
                with patch.object(resize.Image, 'open', side_effect=AssertionError('must skip native image work')):
                    self.assertEqual(resize.resize_icons(BuildState(state.path)), ready)

    def test_save_resume_batch_completion_and_deferred_checkpoint(self):
        import io
        from contextlib import redirect_stdout
        import build_icon
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resized, icons = root / 'Resized', root / 'Icons'
            resized.mkdir(); icons.mkdir()
            sources = [resized / f'{n}.png' for n in range(2)]
            for source in sources:
                Image.new('RGBA', (128, 128), 'red').save(source)
            settings = {'folder_name': 'NewTemplate', 'export_format': '.tga'}
            state = BuildState(root / 'state.json', checkpoint_interval=1000)
            control = BuildControl(state, reader=lambda _: 's')
            def stop_batch(settings, jobs, callback, control=None):
                source, output = jobs[0]
                with Image.open(source) as image:
                    image.save(output, 'TGA')
                callback(source, output, None)
                control.request_pause()
                control.boundary()
            def resume_batch(settings, jobs, callback, control=None):
                self.assertEqual(len(jobs), 1)
                for source, output in jobs:
                    with Image.open(source) as image:
                        image.save(output, 'TGA')
                    callback(source, output, None)
            with patch.multiple(build_icon, RESIZED_FOLDER=resized, ICONS_FOLDER=icons), redirect_stdout(io.StringIO()):
                with patch.object(build_icon, 'render_batch', side_effect=stop_batch):
                    with self.assertRaises(SaveAndExit):
                        build_icon.render_icons(settings, sources, state, control, 'new-v1')
                recovered = BuildState(state.path)
                self.assertEqual(recovered.data['status'], 'saved')
                self.assertEqual(len(recovered.template_history('newtemplate')['records']), 1)
                with patch.object(build_icon, 'render_batch', side_effect=resume_batch):
                    self.assertEqual(build_icon.render_icons(settings, sources, recovered, BuildControl(recovered), 'new-v1'), (1, 1, 0))

    def test_eta_layout(self):
        from console import StageProgress
        with patch('console.perf_counter', side_effect=[0, 10]), patch('console.progress') as show:
            StageProgress(100).update(10, Converted=10)
            self.assertIn('How much longer this shit will be: 1m 30s', show.call_args.args[2])
        with patch('console.perf_counter', side_effect=[0, 1, 11]), patch('console.progress') as show:
            display = StageProgress(100)
            display.set_work_remaining(10)
            display.update(95, work_done=5, Rendered=5, Reused=90)
            self.assertIn('How much longer this shit will be: 10s', show.call_args.args[2])
        from types import SimpleNamespace
        control = SimpleNamespace(paused_seconds=0)
        with patch('console.perf_counter', side_effect=[0, 110]), patch('console.progress') as show:
            display = StageProgress(100, control)
            control.paused_seconds = 100
            display.update(10, Converted=10)
            self.assertIn('How much longer this shit will be: 1m 30s', show.call_args.args[2])

    def test_native_128_blp_pipeline_and_truncated_baseline(self):
        import io
        from contextlib import redirect_stdout
        import build_icon
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blp, png, resized, review, icons = [root / name for name in ('BLP', 'PNG', 'Resized', 'Review', 'Icons')]
            blp.mkdir(); icons.mkdir()
            source = blp / 'Native.BLP'
            Image.new('RGB', (128, 128), (40, 80, 120)).convert('P').save(source, 'BLP')
            state = BuildState(root / 'state.json')
            with patch.multiple(convert, BLP_FOLDER=blp, PNG_FOLDER=png), patch.multiple(resize,
                    PNG_FOLDER=png, RESIZED_FOLDER=resized, REVIEW_FOLDER=review), redirect_stdout(io.StringIO()):
                converted = convert.convert_blp_to_png(state)
                ready = resize.resize_icons(state, png_files=converted)
                self.assertEqual(len(ready), 1)
                with Image.open(converted[0]) as original, Image.open(ready[0]) as prepared:
                    self.assertEqual(original.tobytes(), prepared.tobytes())
                    self.assertEqual(prepared.size, (128, 128))
            output = icons / 'Native.tga'
            Image.new('RGBA', (128, 128), 'blue').save(output, 'TGA')
            output.write_bytes(output.read_bytes()[:18])  # valid header, no pixels
            def batch(settings, jobs, callback, control=None):
                self.assertEqual(len(jobs), 1)
                for input_file, output_file in jobs:
                    with Image.open(input_file) as image:
                        image.save(output_file, 'TGA')
                    callback(input_file, output_file, None)
            with patch.multiple(build_icon, RESIZED_FOLDER=resized, ICONS_FOLDER=icons), redirect_stdout(io.StringIO()), patch.object(build_icon, 'render_batch', side_effect=batch):
                self.assertEqual(build_icon.render_icons({'folder_name': 'AddedTemplate', 'export_format': '.tga'},
                    ready, state, BuildControl(state), 'template', True), (1, 0, 0))
            with Image.open(output) as image:
                image.load()
                self.assertEqual(image.size, (128, 128))

    def test_batch_launch_failure_reports_without_marking_complete(self):
        import io
        from contextlib import redirect_stdout
        import build_icon
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resized, icons = root / 'Resized', root / 'Icons'
            resized.mkdir(); icons.mkdir()
            source = resized / 'Icon.png'
            Image.new('RGBA', (128, 128), 'red').save(source)
            state = BuildState(root / 'state.json')
            with patch.multiple(build_icon, RESIZED_FOLDER=resized, ICONS_FOLDER=icons), redirect_stdout(io.StringIO()), patch.object(build_icon, 'render_batch', side_effect=OSError('GIMP launch failed')):
                self.assertEqual(build_icon.render_icons({'folder_name': 'Onyx', 'export_format': '.tga'},
                    [source], state, BuildControl(state), 'template'), (0, 0, 1))
            self.assertEqual(state.template_history('Onyx')['records'], {})

    def test_existing_nonstandard_review_copy_is_preserved(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png, resized, review = [root / n for n in ('PNG', 'Resized', 'Review')]
            png.mkdir(); review.mkdir()
            source = png / 'Small.png'
            image = Image.new('RGBA', (32, 32), 'red')
            image.save(source)
            review_file = review / source.name
            image.save(review_file)
            state = BuildState(root / 'state.json')
            state.complete('review', Path(source.name), sha256(source) + ':resize-v1', review_file)
            stamp = review_file.stat().st_mtime_ns
            with patch.multiple(resize, PNG_FOLDER=png, RESIZED_FOLDER=resized, REVIEW_FOLDER=review), redirect_stdout(io.StringIO()), patch.object(resize, 'atomic_write', side_effect=AssertionError('must preserve unchanged review copy')):
                self.assertEqual(resize.resize_icons(state), [])
            self.assertEqual(stamp, review_file.stat().st_mtime_ns)
            self.assertEqual(state.data['stages']['review:small.png']['policy'], 2)

    def test_source_disappearing_during_render_is_not_marked_complete(self):
        import io
        from contextlib import redirect_stdout
        import build_icon
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resized, icons = root / 'Resized', root / 'Icons'
            resized.mkdir(); icons.mkdir()
            source = resized / 'Icon.png'
            Image.new('RGBA', (128, 128), 'red').save(source)
            state = BuildState(root / 'state.json')
            def batch(settings, jobs, callback, control=None):
                for source, output in jobs:
                    with Image.open(source) as image:
                        image.save(output, 'TGA')
                    source.unlink()
                    callback(source, output, None)
            with patch.multiple(build_icon, RESIZED_FOLDER=resized, ICONS_FOLDER=icons), redirect_stdout(io.StringIO()), patch.object(build_icon, 'render_batch', side_effect=batch):
                self.assertEqual(build_icon.render_icons({'folder_name': 'Onyx', 'export_format': '.tga'},
                    [source], state, BuildControl(state), 'template'), (0, 0, 1))
            self.assertEqual(state.template_history('Onyx')['records'], {})

    def test_full_build_reports_cached_bad_blps_separately(self):
        import io
        from contextlib import redirect_stdout
        import build_icon
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blp, png, resized, review, icons = [root / name for name in ('BLP', 'PNG', 'Resized', 'Review', 'Icons')]
            blp.mkdir(); icons.mkdir()
            Image.new('RGB', (128, 128), 'red').convert('P').save(blp / 'Good.blp', 'BLP')
            Image.new('RGB', (32, 32), 'blue').convert('P').save(blp / 'Small.blp', 'BLP')
            (blp / 'Bad.blp').write_bytes(bytes(148))
            output = icons / 'Good.tga'
            Image.new('RGBA', (128, 128), 'green').save(output, 'TGA')
            stamp = output.stat().st_mtime_ns
            template_path = root / 'template.xcf'
            template_path.write_bytes(b'fixture template fingerprint')
            settings = {'name': 'Onyx', 'icon_size': 128, 'export_format': '.tga',
                        'replace_layer': 'ICON', 'template_path': template_path}
            state = BuildState(root / 'state.json')
            with patch.multiple(convert, BLP_FOLDER=blp, PNG_FOLDER=png), patch.multiple(resize,
                    PNG_FOLDER=png, RESIZED_FOLDER=resized, REVIEW_FOLDER=review), patch.multiple(build_icon,
                    RESIZED_FOLDER=resized, ICONS_FOLDER=icons), patch.object(build_icon, 'select_template', return_value='Onyx'), patch.object(build_icon, 'load_template', side_effect=lambda _: (dict(settings), root)), patch.object(build_icon, 'validate_template', return_value=(True, None)), patch.object(build_icon, 'render_batch') as renderer:
                first_output = io.StringIO()
                with patch('builtins.input', side_effect=['1', '1']), redirect_stdout(first_output):
                    build_icon.run_build(state, BuildControl(state))
                self.assertEqual(state.data['stage_errors'], 1)
                self.assertEqual(state.data['known_bad_blps'], 0)
                self.assertEqual(state.data['status'], 'incomplete')
                self.assertRegex(first_output.getvalue(), r'New failures\.+ 1')
                recovered = BuildState(state.path)
                second_output = io.StringIO()
                with patch('builtins.input', side_effect=['1', 'y']), redirect_stdout(second_output):
                    build_icon.run_build(recovered, BuildControl(recovered))
                self.assertEqual(recovered.data['stage_errors'], 0)
                self.assertEqual(recovered.data['known_bad_blps'], 1)
                self.assertEqual(recovered.data['review_count'], 1)
                self.assertEqual(recovered.data['status'], 'complete')
                self.assertRegex(second_output.getvalue(), r'Known bad BLPs\.+ 1')
                self.assertRegex(second_output.getvalue(), r'New failures\.+ 0')
                self.assertNotIn('[FAILED]', second_output.getvalue())
                self.assertNotIn('Build completed with 1 error(s)', second_output.getvalue())
                renderer.assert_not_called()
            self.assertEqual(stamp, output.stat().st_mtime_ns)

    def test_corrupt_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            path.write_text('{broken')
            with self.assertRaises(ValueError):
                BuildState(path)


if __name__ == '__main__':
    unittest.main()
