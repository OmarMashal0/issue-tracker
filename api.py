from flask_restful import Resource, Api, reqparse
from db import get_items, get_item, add_item, update_item, delete_item

api = Api()
class ItemList(Resource):
    def get(self): return {'items': get_items()}, 200  # Get all items
    def post(self):  # Add new item
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        parser.add_argument('description', default='')  # Add with default
        parser.add_argument('status', default='Open')
        parser.add_argument('priority', type=int, default=3)
        parser.add_argument('assignee', default='')
        args = parser.parse_args()
        add_item(args)
        return {'message': 'Item added'}, 201
class Item(Resource):
    def get(self, item_id):  # Get one item
        item = get_item(item_id)
        return item if item else {'error': 'Not found'}, 404
    def put(self, item_id):  # Update item
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        args = parser.parse_args()
        args['id'] = item_id
        update_item(args)
        return {'message': 'Item updated'}, 200
    def delete(self, item_id):  # Delete item
        delete_item(item_id)
        return {'message': 'Item deleted'}, 200
api.add_resource(ItemList, '/api/items')
api.add_resource(Item, '/api/items/<item_id>')