from flask_restful import Resource

# ensure bound dataset method
import datalad.distribution.subdatasets

from datalad_webapp import verify_authentication


class Subdataset(Resource):
    def __init__(self, dataset):
        self.ds = dataset

    @verify_authentication
    def get(self):
        return self.ds.subdatasets()
