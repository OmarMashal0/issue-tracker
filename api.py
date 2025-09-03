from flask_restful import Resource, Api, reqparse
from flask_login import login_required, current_user
from db import get_items, get_item, add_item, update_item, delete_item

api = Api()

class ItemList(Resource):
    @login_required
    def get(self):
        return {'items': get_items(current_user.id)}, 200

    @login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        parser.add_argument('description', default='')
        parser.add_argument('status', default='Open')
        parser.add_argument('priority', type=int, default=3)
        parser.add_argument('assignee', default='')
        args = parser.parse_args()
        args['user_id'] = current_user.id
        add_item(args)
        return {'message': 'Item added'}, 201


class Item(Resource):
    @login_required
    def get(self, item_id):
        item = get_item(item_id, current_user.id)
        return item if item else {'error': 'Not found'}, 404

    @login_required
    def put(self, item_id):
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        parser.add_argument('description', default='')
        parser.add_argument('status', default='Open')
        parser.add_argument('priority', type=int, default=3)
        parser.add_argument('assignee', default='')
        args = parser.parse_args()
        args['id'] = item_id
        update_item(args)
        return {'message': 'Item updated'}, 200

    @login_required
    def delete(self, item_id):
        deleted = delete_item(item_id, current_user.id)
        if deleted:
            return {'message': 'Item deleted'}, 200
        else:
            return {'error': 'Not allowed'}, 403


api.add_resource(ItemList, '/api/items')
api.add_resource(Item, '/api/items/<item_id>')
