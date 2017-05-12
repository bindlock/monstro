def Or(query):
    return {'$or': [{key: value} for key, value in query.items()]}


def Regex(query):
    return {key: {'$regex': value} for key, value in query.items()}


class Raw(object):

    def __init__(self, query):
        self.query = query
