from flask import Flask, render_template_string, request, redirect, url_for
import subprocess
import tempfile
import os
from threading import Thread

app = Flask(__name__)

# Store running processes by ID
processes = {}

template_index = """
<!doctype html>
<title>reconFTW Web GUI</title>
<h1>reconFTW Web Interface</h1>
<form action="{{ url_for('run') }}" method="post" enctype="multipart/form-data">
  <label>Domain: <input type="text" name="domain"></label><br>
  <label>Company: <input type="text" name="company"></label><br>
  <label>Targets List: <input type="file" name="listfile"></label><br>
  <label>OOS List: <input type="file" name="oosfile"></label><br>
  <label>Include List: <input type="file" name="infile"></label><br>
  <label>Mode:
    <select name="mode">
      <option value="-r">Recon</option>
      <option value="-s">Subdomains</option>
      <option value="-p">Passive</option>
      <option value="-a">All</option>
      <option value="-w">Web</option>
      <option value="-n">OSINT</option>
      <option value="-z">Zen</option>
    </select>
  </label><br>
  <label>Custom Function: <input type="text" name="custom"></label><br>
  <label>Config File: <input type="file" name="cfgfile"></label><br>
  <label>Output Path: <input type="text" name="output"></label><br>
  <label>Rate Limit: <input type="number" name="rate"></label><br>
  <label><input type="checkbox" name="ai"> AI analysis</label><br>
  <label><input type="checkbox" name="deep"> Deep scan</label><br>
  <label><input type="checkbox" name="vps"> VPS</label><br>
  <label><input type="checkbox" name="checktools"> Check tools</label><br>
  <button type="submit">Run</button>
</form>
"""

template_output = """
<!doctype html>
<title>reconFTW Output</title>
<h1>Command Output</h1>
<pre id="output"></pre>
<script>
  var es = new EventSource("{{ url_for('stream', task_id=task_id) }}");
  es.onmessage = function(e){
    var pre = document.getElementById('output');
    pre.textContent += e.data + "\n";
    window.scrollTo(0, document.body.scrollHeight);
  };
</script>
"""

@app.route('/')
def index():
    return render_template_string(template_index)

@app.route('/run', methods=['POST'])
def run():
    mode = request.form.get('mode', '-r')
    domain = request.form.get('domain', '').strip()
    company = request.form.get('company', '').strip()
    list_file = request.files.get('listfile')
    oos_file = request.files.get('oosfile')
    in_file = request.files.get('infile')
    custom = request.form.get('custom', '').strip()
    cfg_file = request.files.get('cfgfile')
    output_path = request.form.get('output', '').strip()
    rate_limit = request.form.get('rate', '').strip()
    temp_paths = []

    cmd = ['./reconftw.sh', mode]
    if domain:
        cmd.extend(['-d', domain])
    if company:
        cmd.extend(['-m', company])
    if list_file and list_file.filename:
        temp = tempfile.NamedTemporaryFile(delete=False)
        list_file.save(temp.name)
        temp_paths.append(temp.name)
        cmd.extend(['-l', temp.name])
    if oos_file and oos_file.filename:
        temp = tempfile.NamedTemporaryFile(delete=False)
        oos_file.save(temp.name)
        temp_paths.append(temp.name)
        cmd.extend(['-x', temp.name])
    if in_file and in_file.filename:
        temp = tempfile.NamedTemporaryFile(delete=False)
        in_file.save(temp.name)
        temp_paths.append(temp.name)
        cmd.extend(['-i', temp.name])
    if custom:
        cmd.extend(['-c', custom])
    if cfg_file and cfg_file.filename:
        temp = tempfile.NamedTemporaryFile(delete=False)
        cfg_file.save(temp.name)
        temp_paths.append(temp.name)
        cmd.extend(['-f', temp.name])
    if output_path:
        cmd.extend(['-o', output_path])
    if rate_limit:
        cmd.extend(['-q', rate_limit])
    if 'ai' in request.form:
        cmd.append('-y')
    if 'deep' in request.form:
        cmd.append('--deep')
    if 'vps' in request.form:
        cmd.append('-v')
    if 'checktools' in request.form:
        cmd.append('--check-tools')

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    task_id = str(proc.pid)
    processes[task_id] = (proc, temp_paths)
    return redirect(url_for('output', task_id=task_id))

@app.route('/output/<task_id>')
def output(task_id):
    if task_id not in processes:
        return 'Invalid task ID', 404
    return render_template_string(template_output, task_id=task_id)

@app.route('/stream/<task_id>')
def stream(task_id):
    if task_id not in processes:
        return 'Invalid task ID', 404
    proc, temp_paths = processes[task_id]
    def generate():
        for line in proc.stdout:
            yield f"data: {line.rstrip()}\n\n"
        proc.wait()
        for path in temp_paths:
            os.unlink(path)
        yield f"data: Process exited with code {proc.returncode}\n\n"
    return app.response_class(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=False)
