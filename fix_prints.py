import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Early exit if we already injected logger
    if 'import salesbud.utils.logger as logger' in content or 'from salesbud.utils import logger' in content:
        # Well, we might still need to fix prints
        pass

    # For main.py, prevent print_json from being suppressed
    if filepath.endswith('main.py'):
        content = content.replace(
            'print(json.dumps({"success": success, "count": count, "data": data, "errors": errors}))',
            'import sys\n    sys.stdout.write(json.dumps({"success": success, "count": count, "data": data, "errors": errors}) + "\\n")'
        )
        content = content.replace('global QUIET_MODE', 'from salesbud.utils import logger\n    logger.set_quiet_mode(quiet)')
        content = content.replace('QUIET_MODE = quiet', '')
        # Remove QUIET_MODE = False
        content = content.replace('QUIET_MODE = False', '')

    # Replace print(  with logger.print_text( 
    # Must use regex to avoid replacing traceback.print_exc() or pprint()
    # \bprint\(
    content = re.sub(r'(?<!\.)\bprint\s*\(', 'logger.print_text(', content)

    if content != original:
        # Add import at the top
        # Find first import or after module docstring
        import_stmt = "import salesbud.utils.logger as logger\n"
        if "import salesbud.utils.logger" not in content:
            if "import " in content or "from " in content:
                # insert after the first line that looks like an import
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        lines.insert(i, import_stmt.strip())
                        break
                content = '\n'.join(lines)
            else:
                content = import_stmt + content

        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")

def main():
    base_dir = '/Users/guestr/Desktop/syntolabs/salesbud/src/salesbud'
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py') and file != 'logger.py':
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
