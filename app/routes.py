from flask import request, Blueprint, Response, jsonify, make_response
from app import db
from app.models.task import Task

# wave #2 
from sqlalchemy import asc, desc
# wave 3 
from datetime import datetime
# wave 4 
import requests
from app import slack_token 


tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

@tasks_bp.route("", methods=["GET", "POST"])
def all_tasks():
    if request.method == "GET":
        sort = request.args.get("sort")
        if sort == "asc": 
            tasks = Task.query.order_by(asc("title"))
        elif sort == "desc":
            tasks = Task.query.order_by(desc("title"))     
        else:
            tasks = Task.query.all()
        
        tasks_response =[]
        for task in tasks:
            tasks_response.append(task.to_json())
        
        return jsonify(tasks_response)
    
    elif request.method == "POST":
        request_body = request.get_json()
        # Create a Task: Invalid Task With Missing Data
        if "title" not in request_body or "description" not in request_body or "completed_at" not in request_body:
            return make_response ({"details": "Invalid data"}),400
        else:
            new_task = Task(title=request_body["title"],
                    description=request_body["description"],
                    completed_at=request_body["completed_at"])
        db.session.add(new_task)
        db.session.commit()
# this needs to return task that was added in a dict and 201 code 
        return make_response({"task": new_task.to_json()}), 201 



@tasks_bp.route("/<task_id>", methods=["GET", "PUT", "DELETE"])
def one_task_only(task_id):
    task = Task.query.get(task_id)
    
    # GET/PUT/DELETE request to /tasks/1 when there are no matching tasks and get this response
    if task == None:
        return make_response("",404)

    if request.method == "GET":
        return make_response({"task" : task.to_json()}), 200
    elif request.method == "PUT":
        # converting postman json to a dict table
        form_data = request.get_json()

        task.title = form_data["title"]
        task.description = form_data["description"]

        db.session.commit()
        return make_response({"task" : task.to_json()}), 200
    
    elif request.method == "DELETE":
# DELETE requests do not generally include a request body, so 
# no additional planning around the request body is needed        
        db.session.delete(task)
        db.session.commit()
        return make_response ({"details": f'Task {task.task_id} "{task.title}" successfully deleted'})




#wave #3 
@tasks_bp.route("/<task_id>/mark_complete", methods=["PATCH"])
def edit_one_task_complete(task_id):
    task = Task.query.get(task_id)

    if task == None:
        return make_response("",404)
# creating a connection with slack api 
    url = "https://slack.com/api/chat.postMessage"
    data = {
        "channel" : "C021A7E1AE6",
        "text": (f"Someone just completed the task {task.title}")
    }
    headers = {
        "Authorization": slack_token
    }
    connect = requests.post(url, data=data, headers=headers)
    
        
    task.completed_at = datetime.utcnow()
    db.session.commit()

    return make_response({"task" : task.to_json()}), 200


@tasks_bp.route("/<task_id>/mark_incomplete", methods=["PATCH"])
def edit_one_task_incomplete(task_id):
    task = Task.query.get(task_id)
    
    if task == None:
        return make_response("",404)

    task.completed_at = None
    db.session.commit()
    
    return make_response({"task" : task.to_json()}), 200