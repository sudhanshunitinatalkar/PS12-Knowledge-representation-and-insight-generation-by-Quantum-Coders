import os
import pandas as pd
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from werkzeug.utils import secure_filename
from src.data_process.CPU_data_preprocessor_for_visualisation import process_csv
from src.data_process.visuals_generator import generate_plot
from src.data_process.CPU_insight_generator_complete import aio_insights
import threading
import matplotlib
matplotlib.use('Agg')
import shutil
from src.data_process.chatbox import chatbox
import glob

app = Flask(
    __name__,
    # path to templates and static files
    template_folder=os.path.join(os.getcwd(), 'src', 'templates'),
    static_folder=os.path.join(os.getcwd(), 'src', 'static')
)
app.config['SECRET_KEY'] = 'Website-Secret-Key'

# processing folders for visualization
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'src', 'visuals_upload')
app.config['PROCESSED_FOLDER'] = os.path.join(os.getcwd(), 'src', 'visuals_processed')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# processing folders for insights
app.config['INSIGHT_UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'src', 'insights_upload')
app.config['INSIGHT_PROCESSED_FOLDER'] = os.path.join(os.getcwd(), 'src', 'insights_processed')
os.makedirs(app.config['INSIGHT_UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['INSIGHT_PROCESSED_FOLDER'], exist_ok=True)

# file uploading form for insights
class InsightUploadForm(FlaskForm):
    file = FileField('Upload CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    submit = SubmitField('Upload')

# file uploading form for visualization
class VisualUploadForm(FlaskForm):
    file = FileField('Upload CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    submit = SubmitField('Upload')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# delete files in folder when a new file is uploaded
def delete_files_in_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

# submit form for uploading data for visualization
@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
    form = VisualUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return redirect(url_for('visualize'))
    return render_template('visualize.html', form=form)

# save uploaded data for visualization
@app.route('/api/upload', methods=['POST'])
def upload_file():
    form = VisualUploadForm()
    if form.validate_on_submit():
        # Delete existing files in the relevant folders
        delete_files_in_folder(app.config['UPLOAD_FOLDER'])
        delete_files_in_folder(app.config['PROCESSED_FOLDER'])

        # Save the new file
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return jsonify({'success': True, 'message': 'File uploaded successfully'})
    return jsonify({'success': False, 'error': 'Invalid file'})

# preprocess the data and generate report
@app.route('/api/process_data', methods=['GET'])
def process_data():
    input_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.csv')]
    if not input_files:
        return jsonify({'success': False, 'error': 'No CSV file found'})
    
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_files[0])
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], 'output.csv')
    
    def run_processing():
        process_csv(input_path, output_path)
    
    threading.Thread(target=run_processing).start()
    
    # Wait for before.txt to be generated (with a timeout)
    before_path = os.path.join(app.config['PROCESSED_FOLDER'], 'before.txt')
    timeout = 30  # 30 seconds timeout
    start_time = time.time()
    while not os.path.exists(before_path):
        if time.time() - start_time > timeout:
            return jsonify({'success': False, 'error': 'Timeout while generating initial report'})
        time.sleep(0.5)
    
    with open(before_path, 'r') as f:
        before_report = f.read()
    
    return jsonify({'success': True, 'before_report': before_report})

# check if processing is completed
@app.route('/api/check_processing', methods=['GET'])
def check_processing():
    after_path = os.path.join(app.config['PROCESSED_FOLDER'], 'after.txt')
    if os.path.exists(after_path):
        with open(after_path, 'r') as f:
            after_report = f.read()
        return jsonify({'success': True, 'completed': True, 'after_report': after_report})
    else:
        return jsonify({'success': True, 'completed': False})


@app.route('/processed/<path:filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)


# get column names
@app.route('/api/get_columns', methods=['GET'])
def get_columns():
    try:
        df = pd.read_csv(os.path.join(app.config['PROCESSED_FOLDER'], 'output.csv'))
        columns = df.columns.tolist()
        return jsonify({'success': True, 'columns': columns})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# generate visualization
@app.route('/api/visualize', methods=['POST'])
def api_visualize():
    try:
        plot_type = request.form.get('plot-type')
        x_axis = request.form.get('x-axis')
        y_axis = request.form.get('y-axis')

        print("plot_type:", plot_type)
        print("y-axis:", y_axis)
        
        df = pd.read_csv(os.path.join(app.config['PROCESSED_FOLDER'], 'output.csv'))
        
        generate_plot(df, plot_type, x_axis, y_axis)
        
        return jsonify({'success': True, 'message': 'Visualization generation started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    

# check if visualization is completed
@app.route('/api/check_visualization', methods=['GET'])
def check_visualization():
    plot_type = request.args.get('plot_type')
    x_axis = request.args.get('x_axis')
    y_axis = request.args.get('y_axis')

    # print("plot_type:", plot_type)
    
    if plot_type in ['correlation_matrix', 'pie_chart']:
        filename = f"{plot_type}_{x_axis}.png" if x_axis else f"{plot_type}.png"
    else:
        filename = f"{plot_type}_{x_axis}_{y_axis}.png"
    
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], 'visual_images', filename)

    print('file_path', file_path)
    
    if os.path.exists(file_path):
        return jsonify({'success': True, 'image_url': f'/processed/visual_images/{filename}'})
    else:
        print("here")
        return jsonify({'success': False})
    
# submit form for uploading data for insights
@app.route('/insights', methods=['GET', 'POST'])
def insights():
    form = InsightUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['INSIGHT_UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return redirect(url_for('insights'))
    return render_template('insights.html', form=form)

# save uploaded data for insights
@app.route('/api/upload_insight', methods=['POST'])
def upload_file_insight():
    form = InsightUploadForm()
    if form.validate_on_submit():
        # Delete existing files in the relevant folders
        delete_files_in_folder(app.config['INSIGHT_UPLOAD_FOLDER'])
        delete_files_in_folder(app.config['INSIGHT_PROCESSED_FOLDER'])

        # Save the new file
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['INSIGHT_UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return jsonify({'success': True, 'message': 'File uploaded successfully'})
    return jsonify({'success': False, 'error': 'Invalid file'})

# preprocess data for insights
@app.route('/api/process_data_insight', methods=['GET'])
def process_data_insight():
    input_files = [f for f in os.listdir(app.config['INSIGHT_UPLOAD_FOLDER']) if f.endswith('.csv')]
    if not input_files:
        return jsonify({'success': False, 'error': 'No CSV file found'})
    
    input_path = os.path.join(app.config['INSIGHT_UPLOAD_FOLDER'], input_files[0])
    output_path = os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'])
    
    def run_processing_insight():
        aio_insights(input_path, output_path)
    
    threading.Thread(target=run_processing_insight).start()
    
    # Wait for before.txt to be generated (with a timeout)
    before_path = os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'], 'before.txt')
    print('befoe path', before_path)
    timeout = 60  # 30 seconds timeout
    start_time = time.time()
    while not os.path.exists(before_path):
        if time.time() - start_time > timeout:
            return jsonify({'success': False, 'error': 'Timeout while generating initial report'})
        time.sleep(0.5)
    
    with open(before_path, 'r') as f:
        before_report = f.read()
        print("before report", before_report)
    
    return jsonify({'success': True, 'before_report': before_report})

# check if processing is completed
@app.route('/api/check_processing_insight', methods=['GET'])
def check_processing_insight():
    after_path = os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'], 'after.txt')
    if os.path.exists(after_path):
        with open(after_path, 'r') as f:
            after_report = f.read()
        return jsonify({'success': True, 'completed': True, 'after_report': after_report})
    else:
        return jsonify({'success': True, 'completed': False})
    

# check if report is generated
@app.route('/api/check_report_insight', methods=['GET'])
def check_report_insight():
    report_path = os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'], 'generated_report.txt')
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report_path = f.read()
        return jsonify({'success': True, 'completed': True, 'insight_report': report_path})
    else:
        return jsonify({'success': True, 'completed': False})


# send processed data for insights
@app.route('/processed_insight/<path:filename>')
def processed_file_insight(filename):
    return send_from_directory(app.config['INSIGHT_PROCESSED_FOLDER'], filename)


# get columns for insights
@app.route('/api/get_columns_insight', methods=['GET'])
def get_columns_insight():
    try:
        df = pd.read_csv(os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'], 'output.csv'))
        columns = df.columns.tolist()
        return jsonify({'success': True, 'columns': columns})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# generate report
@app.route('/api/generate_report', methods=['GET'])
def generate_report():
    try:
        # Read the generated report
        with open(os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'], 'generated_report.txt'), 'r') as f:
            report_content = f.read()

        # Get all image files in the processed_insight folder
        image_files = glob.glob(os.path.join(app.config['INSIGHT_PROCESSED_FOLDER'], '*.png'))
        image_urls = [f'/processed_insight/{os.path.basename(file)}' for file in image_files]

        return jsonify({
            'success': True,
            'report': report_content,
            'images': image_urls
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
# chat query
@app.route('/api/chat_query', methods=['POST'])
def chat_query():
    try:
        data = request.get_json()
        query = data.get('query')
        if not query:
            return jsonify({'success': False, 'error': 'No query provided'})
        
        response = chatbox(query)
        if response is None:
            return jsonify({'success': False, 'error': 'Failed to get response from chatbox'})
        
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    


if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)


