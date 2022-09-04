# Tests if string can be cast into float
def str_isfloat(str):
  try:
    float(str)
    return True
  except ValueError:
    return False