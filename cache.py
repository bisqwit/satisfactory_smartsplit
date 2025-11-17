import pickle, os, pathlib
from functools import wraps
from platformdirs import user_cache_dir

def cached(func):
    func.cache = {}
    name = pathlib.Path(user_cache_dir('smartsplit', 'bisqwit'))
    try:
        os.mkdir(name)
    except:
        pass
    file     = name / 'smartsplit.cache'
    file_tmp = name / 'smartsplit.cache.new'
    try:
        with open(file, 'rb') as db:
            func.cache = pickle.load(db)
    except:
        pass
    def save():
        with open(file_tmp, 'wb') as db:
            pickle.dump(func.cache, db)
        os.replace(file_tmp, file)
    cached.save = save

    @wraps(func)
    def wrapper(*args):
        if args in func.cache:
            return func.cache[args]
        else:
            func.cache[args] = result = func(*args)
            return result   
    return wrapper
