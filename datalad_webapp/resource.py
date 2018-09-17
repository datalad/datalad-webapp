from flask_restful import Resource


class WebAppResource(Resource):
    def __init__(self, dataset, read_only=False):
        self.ds = dataset
        self.read_only = read_only
