from flask import render_template, request, redirect, url_for, flash, get_flashed_messages
import os
from app import app
import datetime
from scheduler_set import schedule_trips, read_excel, scheduler
from .forms import FileUploadForm, EditTimeForm
##############################################################################
# 404 route

@app.errorhandler(404) 
def not_found(e): 
  return render_template("404.html")

##############################################################################
# Homepage route

@app.route('/', methods=['GET'])
def list_jobs():
    get_flashed_messages()
    form = FileUploadForm()
    update_form = EditTimeForm()
    scheduled_jobs=scheduler.get_jobs()
    print(scheduled_jobs)
    return render_template('upload.html', form=form, update_form=update_form, jobs=scheduled_jobs)

##############################################################################
# Post file upload route

@app.route('/upload', methods=['POST'])
def upload_file():
    form = FileUploadForm()
    
    if form.validate_on_submit():
        # Get the uploaded file and save it to the Upload folder
        file = form.file.data
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)  
        try:
            # Read the saved file
            trips = read_excel(file_path)
            # Pass the data from the file to schedule the trips
            response = schedule_trips(trips)
            # Remove the file from the upload folder
            os.remove(file_path)
            
            flash('Successfully scheduled all upcoming trips', 'success')

            if len(response) > 0:
                flash(f'The following trips departure times have already passed: {", ".join(response)}', 'warning')
            return redirect(url_for('list_jobs'))
        except Exception as e:
            # If error before scheduling - remove the file
            os.remove(file_path)
            flash(str(e), 'danger')
        
    return render_template('upload.html', form=form)

##############################################################################
# Post delete scheduled job route

@app.route('/delete_job/<job_id>', methods=['POST'])
def delete_job(job_id):
    try:
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
            flash(f'Trip {job_id} deleted!', 'warning')
        return redirect(url_for('list_jobs'))
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('list_jobs'))

##############################################################################
# Post edit trip departure time for a scheduled job

@app.route('/edit_job/<job_id>', methods=['POST'])
def edit_job(job_id):
    update_form = EditTimeForm()
    if update_form.validate_on_submit():
        # Get the new time from the form
        new_time = update_form.new_time.data
        now = datetime.datetime.now()
        # Calculate to run the job one hour prior to the trip time
        new_run_date = datetime.datetime.combine(now.date(), new_time) - datetime.timedelta(hours=1)
        try:
            # Get the job from the job store
            job = scheduler.get_job(job_id)
            if job:
                # Reschedule with the new run time
                job.reschedule('date', run_date=new_run_date)
                flash(f'Trip {job_id} successfully edited!', 'success')
            return redirect(url_for('list_jobs'))
        except Exception as e:
            flash(str(e), 'danger')
            return redirect(url_for('list_jobs'))