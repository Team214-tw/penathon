from typing import (
    Callable,
    Any,
    Union,
    Dict,
    List,
    TypeVar,
    Tuple,
    Set,
    Sequence,
    get_type_hints,
    TextIO,
    Optional,
    IO,
    BinaryIO,
    Type,
    Generator,
    overload,
    Iterable,
    AsyncIterable,
    Iterator,
    AsyncIterator,
    AbstractSet,
    AnyStr,
)
import copy


def check(provided, expected):
    if isinstance(provided, TypeVar):
        if len(provided.__constraints__) == 0:
            return True
        else:
            for con in provided.__constraints__:
                result = check(con, expected)
                if result == False:
                    return False
        return True

    if isinstance(expected, TypeVar):
        if len(expected.__constraints__) == 0:
            return True
        else:
            for con in expected.__constraints__:
                result = check(provided, con)
                if result:
                    return True
            else:
                return False

    originP = getattr(provided, "__origin__", provided)
    originE = getattr(expected, "__origin__", expected)

    if originP is Any:
        return True

    if originE is Any:
        return True

    if originP is Union:
        for con in provided.__args__:
            result = check(con, expected)
            if result == False:
                return False
        return True

    if originE is Union:
        for con in expected.__args__:
            result = check(provided, con)
            if result:
                return True
        else:
            return False

    if (
        (originP is None and originE is not None)
        or (originE is None and originP is not None)
        or (not issubclass(originP, originE))
    ):
        return False

    argP = getattr(provided, "__args__", [])
    argE = getattr(expected, "__args__", [])

    if len(argP) == 0 and len(argE) == 0:
        return True

    if len(argP) != len(argE):
        return False

    args = zip(argP, argE)

    for argP, argE in args:
        result = check(argP, argE)
        if result == False:
            break
    else:
        return True

    return False


def main():
    x = List[int]
    y = Iterable[int]
    res = check(x, y)
    print(x)
    print(y)
    print(res)
    print("")

    x = Iterable[int]
    y = List[int]
    res = check(x, y)
    print(x)
    print(y)
    print(res)
    print("")

    x = List[int]
    y = TypeVar("T", Iterable[int], int)
    res = check(x, y)
    print(x)
    print(y)
    print(res)
    print("")

    x = str
    y = AnyStr
    res = check(x, y)
    print(x)
    print(y)
    print(res)
    print("")

    x = int
    y = Union[str, int]
    res = check(x, y)
    print(x)
    print(y)
    print(res)
    print("")

    x = int
    y = Union[str, None]
    res = check(x, y)
    print(x)
    print(y)
    print(res)
    print("")

    x = int
    y = Optional[int]
    res = check(x, y)

    print(x)
    print(y)
    print(res)
    print("")


if __name__ == "__main__":
    main()
