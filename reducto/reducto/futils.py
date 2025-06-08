

def k_cut(k, str_to_cut):
    return str_to_cut[0:min(k, len(str_to_cut))]


def set_closure_by_elems(vals, method):
    res = vals.copy()
    to_process = vals.copy()
    while to_process:
        current = to_process.pop()
        for val in method(current):
            if val not in res:
                res.add(val)
                to_process.add(val)
    return res


def map_closure(initial, method):
    res = initial.copy()
    flag = True
    while flag:
        flag = False
        addon = method(res)
        for key, value in addon.items():
            value = set(value)
            if key not in res:
                flag = True
                res[key] = value
                continue
            if not value.issubset(res[key]):
                flag = True
                res[key] |= value
                continue
    return res


def set_closure(vals, method):
    res = vals.copy()
    while True:
        addon = method(res)
        if addon.issubset(res):
            return res
        res |= addon
