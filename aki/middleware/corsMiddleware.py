
class corsMiddleware(object):
    def process_response(self, req, resp):
        resp["Access-Control-Allow-Origin"] = "*"
        resp["Access-Control-Allow-Headers"] = "*"
        resp['Bro'] = 'BROOOOOOOOOOOOOOO'
        return resp