from flask import jsonify
from flask_restful import Resource, abort
from data import db_session
from data.tasks import Tasks


def abort_if_tasks_not_found(tasks_id):
    session = db_session.create_session()
    tasks = session.query(Tasks).get(tasks_id)
    if not tasks:
        abort(404, message=f"Tasks {tasks_id} not found")


class TasksListResource(Resource):
    def get(self):
        session = db_session.create_session()
        tasks = session.query(Tasks).all()
        lst = []
        for item in tasks:
            lst.append(
                {'task': item.task, 'category_id': item.category_id, 'date': item.date, 'importance': item.importance,
                 'is_complete': item.is_complete, 'user_id': item.user_id})
        return jsonify({'tasks': lst})
