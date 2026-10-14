from PIL import Image
from utils import (PNG_FOLDER, RESIZED_FOLDER, REVIEW_FOLDER,
                   BuildState, discover, sha256, atomic_write, path_key, image_matches)
from console import StageProgress

CROP_BOX = (6, 6, 122, 122)


def resize_icons(state=None, control=None, png_files=None):
    state = state or BuildState()
    ready = []
    processed = skipped = review = errors = 0
    files = discover(PNG_FOLDER, '.png') if png_files is None else png_files
    display = StageProgress(len(files), control)
    print(f'Checking {len(files)} PNG file(s); unchanged resized PNGs are reused.')
    for index, source in enumerate(files, start=1):
        if control:
            control.boundary()
        relative = source.relative_to(PNG_FOLDER)
        output = RESIZED_FOLDER / relative
        review_file = REVIEW_FOLDER / relative
        try:
            fingerprint = sha256(source) + ':resize-v1'
            # Skip opening/resizing images whose completed records still match.
            if state.current('resize', relative, fingerprint, output):
                skipped += 1
                ready.append(output)
            elif (state.current('review', relative, fingerprint, review_file)
                  and state.data['stages'].get('review:' + path_key(relative), {}).get('policy') == 2):
                output.unlink(missing_ok=True)
                review += 1
            else:
                with Image.open(source) as image:
                    image = image.convert('RGBA')
                    if image.size not in ((64, 64), (128, 128)):
                        if not state.current('review', relative, fingerprint, review_file):
                            atomic_write(review_file, lambda p: image.save(p, 'PNG'))
                            state.complete('review', relative, fingerprint, review_file)
                        state.data['stages']['review:' + path_key(relative)]['policy'] = 2
                        state.checkpoint()
                        output.unlink(missing_ok=True)
                        review += 1
                    else:
                        if image.size == (64, 64):
                            image = image.resize((128, 128), Image.Resampling.LANCZOS)
                            image = image.crop(CROP_BOX).resize((128, 128), Image.Resampling.LANCZOS)
                        # Native 128x128 inputs preserve their pixels and dimensions.
                        reuse_existing = (
                            'resize:' + path_key(relative) not in state.data['stages']
                            and output.is_file() and image_matches(output, image))
                        if not reuse_existing:
                            atomic_write(output, lambda p: image.save(p, 'PNG'))
                        state.complete('resize', relative, fingerprint, output)
                        if reuse_existing:
                            skipped += 1
                        else:
                            processed += 1
                        ready.append(output)
        except Exception as exc:
            errors += 1
            print(f'\n[FAILED] {relative}: {exc}')
        display.update(index, Resized=processed, Reused=skipped, Review=review, Failed=errors)
    print(f'Resized: {processed}  Reused: {skipped}  Review: {review}  Failed: {errors}')
    state.data['stage_errors'] = state.data.get('stage_errors', 0) + errors
    state.data['review_count'] = review
    state.save()
    return ready


if __name__ == '__main__':
    resize_icons()
