class State():
    def __init__(self, db, path=None):
        if path is None: path = db.path + ".cache"

        # TODO: Load from master DB
        self.db_metadata = db.get_all_metadata()

        pass # TODO: Save and load from cache

    def sensors(self):
        return self.db_metadata

    def update(self, event):
        pass # TODO

    def close(self):
        pass # TOO
