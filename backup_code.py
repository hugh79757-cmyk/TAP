import os
from pathlib import Path

TARGET_EXTENSIONS = {'.py', '.yaml', '.yml', '.md', '.txt'}
IGNORE_DIRS = {'venv', '.git', '__pycache__', '.idea', '.vscode', 'node_modules', 'cache', 'logs', 'output'}
IGNORE_FILES = {'poetry.lock', 'package-lock.json', 'project_backup.txt', '.DS_Store', 'backup_code.py'}

def create_backup():
    root_dir = Path('/Users/twinssn/Desktop/tour-auto-publisher')
    output_file = root_dir / 'project_backup.txt'
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("=" * 60 + "\n")
        outfile.write("TOUR AUTO PUBLISHER - PROJECT BACKUP\n")
        outfile.write("=" * 60 + "\n\n")
        
        outfile.write("=== PROJECT STRUCTURE ===\n\n")
        for path in sorted(root_dir.rglob('*')):
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            rel_path = path.relative_to(root_dir)
            depth = len(rel_path.parts)
            if path.is_dir():
                outfile.write(f"{'  ' * (depth-1)}📂 {path.name}/\n")
            else:
                outfile.write(f"{'  ' * (depth-1)}📄 {path.name}\n")
        
        outfile.write("\n\n" + "=" * 60 + "\n")
        outfile.write("=== FILE CONTENTS ===\n")
        outfile.write("=" * 60 + "\n\n")

        for path in sorted(root_dir.rglob('*')):
            if path.is_dir():
                continue
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            if path.name in IGNORE_FILES:
                continue
            if path.suffix not in TARGET_EXTENSIONS:
                continue

            try:
                content = path.read_text(encoding='utf-8')
                rel_path = path.relative_to(root_dir)
                outfile.write(f"\n### FILE: {rel_path}\n")
                outfile.write("-" * 60 + "\n")
                outfile.write(content)
                outfile.write("\n" + "=" * 60 + "\n")
                print(f"✅ Backup: {rel_path}")
            except Exception as e:
                print(f"❌ Skip {path}: {e}")

    print(f"\n🎉 완료! project_backup.txt 생성됨")

if __name__ == '__main__':
    create_backup()
