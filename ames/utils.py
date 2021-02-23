def is_in_range(year_arg, year):
    # Is a given year in the range of a year argument YEAR-YEAR or YEAR?
    if year_arg != None:
        split = year_arg.split("-")
        if len(split) == 2:
            if int(year) >= int(split[0]) and int(year) <= int(split[1]):
                return True
        else:
            if year == split[0]:
                return True
    else:
        return True
    return False
