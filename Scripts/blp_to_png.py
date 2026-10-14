from pathlib import Path
import struct
from PIL import Image

from utils import (BLP_FOLDER, PNG_FOLDER, BuildState, discover, sha256,
                   atomic_write, path_key, image_matches)
from console import StageProgress


class InvalidBLP(ValueError):
    pass


def load_blp(source):
    """Return a detached RGBA image; validate raw BGRA mip bounds first."""
    source = Path(source)
    with source.open('rb') as stream:
        header = stream.read(148)
        if header[:4] not in (b'BLP1', b'BLP2'):
            raise InvalidBLP('Invalid BLP header; re-extract this file from the source archive')
        if header[:4] == b'BLP2':
            if len(header) < 148:
                raise InvalidBLP('Truncated BLP2 header; re-extract this file')
            if header[8] == 3:
                if struct.unpack_from('<I', header, 4)[0] != 1:
                    raise InvalidBLP('Unsupported BLP2 raw texture type')
                width, height = struct.unpack_from('<II', header, 12)
                if not width or not height or (Image.MAX_IMAGE_PIXELS is not None
                        and width * height > Image.MAX_IMAGE_PIXELS):
                    raise InvalidBLP('Invalid or excessive BLP2 dimensions')
                if header[9] not in (0, 1, 4, 8):
                    raise InvalidBLP('Invalid BLP2 alpha depth')
                offset = struct.unpack_from('<I', header, 20)[0]
                length = struct.unpack_from('<I', header, 84)[0]
                expected = width * height * 4
                size = stream.seek(0, 2)
                if offset < 148 or length < expected or offset + length > size:
                    raise InvalidBLP('Truncated or invalid BLP2 BGRA mipmap; re-extract this file')
                stream.seek(offset)
                pixels = stream.read(expected)
                if len(pixels) != expected:
                    raise InvalidBLP('Truncated BLP2 BGRA pixels')
                image = Image.frombytes('RGBA', (width, height), pixels, 'raw', 'BGRA')
                if header[9] == 0:
                    image.putalpha(255)
                return image
    with Image.open(source) as image:
        return image.convert('RGBA')


def convert_blp_to_png(state=None, control=None):
    state = state or BuildState()
    ready = []
    converted = skipped = failed = known_bad = 0
    files = discover(BLP_FOLDER, '.blp')
    total = len(files)
    print(f'Checking {total} BLP file(s); unchanged successful PNGs are reused.')
    display = StageProgress(total, control)
    for index, source in enumerate(files, start=1):
        if control:
            control.boundary()
        relative = source.relative_to(BLP_FOLDER)
        output = PNG_FOLDER / relative.with_suffix('.png')
        try:
            fingerprint = sha256(source)
            if state.failure('convert', relative, fingerprint):
                known_bad += 1
            elif state.current('convert', relative, fingerprint, output):
                skipped += 1
                ready.append(output)
            else:
                # Cache source decoding failures, never filesystem/export failures.
                try:
                    image = load_blp(source)
                except (FileNotFoundError, PermissionError):
                    raise
                except Exception as exc:
                    if sha256(source) == fingerprint:
                        state.record_failure('convert', relative, fingerprint, exc)
                    raise
                with image:
                    # Establish missing legacy records by comparing pixels once.
                    # Never bless an unrelated/stale PNG just because it exists.
                    entry = state.data['stages'].get('convert:' + path_key(relative))
                    reuse_existing = entry is None and output.is_file() and image_matches(output, image)
                    def write(path):
                        image.save(path, 'PNG')
                    if not reuse_existing:
                        atomic_write(output, write)
                if sha256(source) != fingerprint:
                    raise RuntimeError('BLP changed during conversion; retry next run')
                state.complete('convert', relative, fingerprint, output)
                if reuse_existing:
                    skipped += 1
                else:
                    converted += 1
                ready.append(output)
        except Exception as exc:
            failed += 1
            print(f'\n[FAILED] {relative}: {exc}')
        display.update(index, Converted=converted, Reused=skipped,
                       Known_bad=known_bad, Failed=failed)
    print(f'Converted: {converted}  Reused PNGs: {skipped}  '
          f'Unchanged bad BLPs skipped: {known_bad}  New failures: {failed}')
    if known_bad:
        print('Unchanged bad files were not decoded again. Details: Logs/build-state.json')
    state.data['stage_errors'] = state.data.get('stage_errors', 0) + failed
    state.data['known_bad_blps'] = known_bad
    state.save()
    return ready


if __name__ == '__main__':
    convert_blp_to_png()
