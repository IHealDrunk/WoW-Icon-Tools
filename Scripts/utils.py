from pathlib import Path
import hashlib
import json
import os
import tempfile
from time import perf_counter

from PIL import Image


# ==========================================================
# Project Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).parent.parent


# ==========================================================
# Working Folders
# ==========================================================

BLP_FOLDER = PROJECT_ROOT / "BLP"
PNG_FOLDER = PROJECT_ROOT / "PNG"
RESIZED_FOLDER = PROJECT_ROOT / "PNG_128x128_Resized"
REVIEW_FOLDER = PROJECT_ROOT / "REVIEW"
ICONS_FOLDER = PROJECT_ROOT / "ICONS"

TEMPLATES_FOLDER = PROJECT_ROOT / "Templates"
LOGS_FOLDER = PROJECT_ROOT / "Logs"


# ==========================================================
# Create Required Folders
# ==========================================================

REQUIRED_FOLDERS = [
    BLP_FOLDER,
    PNG_FOLDER,
    RESIZED_FOLDER,
    REVIEW_FOLDER,
    ICONS_FOLDER,
    TEMPLATES_FOLDER,
    LOGS_FOLDER,
]

for folder in REQUIRED_FOLDERS:
    folder.mkdir(parents=True, exist_ok=True)

# Persistent build records and safe file operations
def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def path_key(path):
    return Path(path).as_posix().casefold()


def discover(root, suffix):
    files = sorted((p for p in root.rglob('*') if p.is_file()
                    and p.suffix.casefold() == suffix.casefold()), key=path_key)
    keys = [path_key(p.relative_to(root)) for p in files]
    if len(keys) != len(set(keys)):
        raise ValueError(f'Case-insensitive path collision in {root}')
    return files


def atomic_write(destination, writer):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.wow-', suffix=destination.suffix,
                                dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        writer(temporary)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError('No complete output was produced')
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def image_matches(path, expected):
    """Compare legacy output pixels before recording them as reusable."""
    try:
        with Image.open(path) as existing:
            return (existing.size == expected.size
                    and existing.convert('RGBA').tobytes() == expected.convert('RGBA').tobytes())
    except (OSError, ValueError):
        return False


class BuildState:
    """Only durable, successfully completed stages may be reused."""
    def __init__(self, path=None, checkpoint_interval=0):
        self.path = Path(path) if path else LOGS_FOLDER / 'build-state.json'
        self.checkpoint_interval = checkpoint_interval
        self.last_saved = perf_counter()
        self.data = {'version': 1, 'template': None, 'status': 'running', 'stages': {}}
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                if (data.get('version') != 1 or not isinstance(data.get('stages'), dict)
                        or not all(isinstance(v, dict) for v in data['stages'].values())):
                    raise ValueError('Unsupported checkpoint format')
                self.data = data
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f'Cannot read checkpoint {self.path}: {exc}. '
                                 'Preserve it and move it aside to rebuild safely.') from exc

        histories = self.data.setdefault('templates', {})
        if (not isinstance(histories, dict) or any(
                not isinstance(history, dict) or not isinstance(history.get('records', {}), dict)
                or any(not isinstance(record, dict) for record in history.get('records', {}).values())
                for history in histories.values())):
            raise ValueError(f'Invalid template history in {self.path}')

    def checkpoint(self):
        if perf_counter() - self.last_saved >= self.checkpoint_interval:
            self.save()

    def save(self):
        def write(path):
            with path.open('w', encoding='utf-8') as stream:
                json.dump(self.data, stream, indent=2, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
        atomic_write(self.path, write)
        self.last_saved = perf_counter()

    def current(self, stage, relative, fingerprint, output):
        entry = self.data['stages'].get(stage + ':' + path_key(relative), {})
        return (entry.get('input') == fingerprint and output.is_file()
                and entry.get('output') == sha256(output))

    def failure(self, stage, relative, fingerprint):
        entry = self.data['stages'].get(stage + ':' + path_key(relative), {})
        if entry.get('input') == fingerprint:
            return entry.get('error')
        return None

    def record_failure(self, stage, relative, fingerprint, reason):
        self.data['stages'][stage + ':' + path_key(relative)] = {
            'input': fingerprint, 'error': str(reason)}
        self.checkpoint()

    def complete(self, stage, relative, fingerprint, output):
        self.data['stages'][stage + ':' + path_key(relative)] = {
            'input': fingerprint, 'output': sha256(output)}
        self.checkpoint()

    def template_history(self, template_name):
        return self.data['templates'].setdefault(
            template_name.casefold(), {'name': template_name, 'records': {}})

    def migrate_render_history(self, template_name, template_fingerprint):
        history = self.template_history(template_name)
        migrated = []
        for key, entry in self.data['stages'].items():
            fingerprint = entry.get('input', '')
            if (key.startswith('render:') and isinstance(fingerprint, str)
                    and fingerprint[64:] == template_fingerprint and entry.get('output')):
                history['records'].setdefault(key[len('render:'):], {
                    'input': fingerprint[:64], 'output': entry['output'],
                    'template': template_fingerprint})
                migrated.append(key)
        for key in migrated:
            del self.data['stages'][key]
        self.save()

    def render_current(self, template_name, relative, source_hash, output):
        record = self.template_history(template_name)['records'].get(path_key(relative), {})
        return (record.get('input') == source_hash and output.is_file()
                and record.get('output') == sha256(output))

    def render_complete(self, template_name, relative, source_hash, output, template_fingerprint):
        self.template_history(template_name)['records'][path_key(relative)] = {
            'input': source_hash, 'output': sha256(output), 'template': template_fingerprint}
        self.checkpoint()


class SaveAndExit(Exception):
    pass


class BuildControl:
    def __init__(self, state, reader=input):
        self.state = state
        self.reader = reader
        self.pause_requested = False
        self.paused_seconds = 0.0

    def pause(self):
        started = perf_counter()
        print('\nPaused. [R] Resume  [S] Save & Exit')
        try:
            while True:
                try:
                    choice = self.reader('Select an option: ').strip().casefold()
                except (EOFError, KeyboardInterrupt):
                    choice = 's'
                if choice == 'r':
                    return
                if choice == 's':
                    self.state.data['status'] = 'saved'
                    self.state.save()
                    raise SaveAndExit()
        finally:
            self.paused_seconds += perf_counter() - started

    def request_pause(self, *_):
        self.pause_requested = True

    def boundary(self):
        if self.pause_requested:
            self.pause_requested = False
            self.pause()
        # Poll only between files; no background thread competes with input().
        import sys
        if os.name == 'nt' and sys.stdin.isatty():
            import msvcrt
            while msvcrt.kbhit():
                key = msvcrt.getwch().casefold()
                if key == 'p':
                    self.pause()
                elif key == 's':
                    self.state.data['status'] = 'saved'
                    self.state.save()
                    raise SaveAndExit()
