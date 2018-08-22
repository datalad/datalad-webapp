from flask_restful import Resource


class WebAppResource(Resource):
    def __init__(self, dataset):
        self.ds = dataset
