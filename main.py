from flask import Flask, request, render_template
import zipfile, os, yaml

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = './upload/'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# def validate_dockerfile(content):
#     try:
#         temp_dockerfile = "temp_dockerfile"
#         with open(temp_dockerfile, "w") as f:
#             f.write(content)
#         client = docker.from_env()
#         client.images.build(path=".", dockerfile=temp_dockerfile, rm=True, pull=False)
#         os.remove(temp_dockerfile)
#         return True
#     except (docker.errors.BuildError, docker.errors.APIError):
#         if os.path.exists("temp_dockerfile"):
#             os.remove("temp_dockerfile")
#         return False

def validate_compose_file(content):
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict) or "services" not in data:
            return False
        if "version" not in data:
            return False
        return True
    except yaml.YAMLError:
        return False

def process_files(extract_dir):
    full_path = app.config['UPLOAD_FOLDER']+extract_dir
    valid_files = []
    invalid_files = []
    for root, _, files in os.walk(full_path):
        print(root)
        for file in files:
            file_path = os.path.join(root, file)
            if file.lower() == "dockerfile":
                with open(file_path, "r") as f:
                    content = f.read()
                # if validate_dockerfile(content):
                #     valid_files.append(file_path)
                # else:
                #     invalid_files.append(file_path)
            elif file.lower().endswith(("yml", "yaml")):
                with open(file_path, "r") as f:
                    content = f.read()
                if validate_compose_file(content):
                    valid_files.append(file_path)
                else:
                    invalid_files.append(file_path)
            elif file.endswith("zip"):
                pass
            else:
                valid_files.append(file_path)
    return valid_files, invalid_files

def extract(archive, dir_name):
    with zipfile.ZipFile(archive, 'r') as z:
        for i in z.infolist():
            with open(os.path.join(app.config['UPLOAD_FOLDER']+dir_name, i.filename), 'wb') as f:
                f.write(z.open(i.filename, 'r').read())

@app.route('/') 
def main():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if request.files and 'archive' in request.files:
            archive = request.files['archive']
            random = os.urandom(16).hex()
            if archive \
                and '.' in archive.filename \
                and archive.filename.rsplit('.', 1)[1].lower() == 'zip':
                random_dir = os.urandom(32).hex()
                os.makedirs(app.config['UPLOAD_FOLDER']+random_dir)
               save_path = os.path.join(f"{app.config['UPLOAD_FOLDER']}{random_dir}/", f"{random}.zip")
                print(save_path)
                archive.save(save_path)
                extract(save_path, random_dir)
                valid_files, invalid_files = process_files(random_dir)
                if invalid_files:
                    error_message = f"Extracted successfully, but some files are invalid: {', '.join(invalid_files)}"
                else:
                    error_message = "App was extracted successfully and all files are valid."
                return render_template('index.html', error=error_message)
        return render_template('index.html', error="Not valid zip file, try again")
    except Exception as e:
         return render_template('index.html', error=f'Error: {e}')

if __name__ == '__main__':
    app.run(port=5050, host='127.0.0.1', debug=True)
