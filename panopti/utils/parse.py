import numpy as np
from typing import Any, Dict, List, Tuple, Union
import numbers
import msgpack



def _is_numeric_scalar(x: Any) -> bool:
    """Check for int/float/np.number (but NOT bool)."""
    return isinstance(x, (numbers.Integral, numbers.Real, np.number)) and not isinstance(x, bool)


def _can_vectorise(seq: Union[List[Any], Tuple[Any, ...]]) -> bool:
    """Return True if *seq* looks like a homogenous numeric 1-D sequence."""
    if not seq:
        return False

    first = seq[0]
    if isinstance(first, (list, tuple)):
        return False

    if _is_numeric_scalar(first):
        return all(_is_numeric_scalar(x) for x in seq)

    return False


def as_array(obj: Any) -> Any:
    """Convert *obj* and (possibly) its children to ``np.ndarray`` if appropriate."""
    if isinstance(obj, np.ndarray): 
        # if obj is a scalar pop it out:
        if obj.ndim == 0:
            return obj.item()
        return obj
    
    if obj is None or _is_numeric_scalar(obj):
        return obj

    if isinstance(obj, dict):
        return {k: as_array(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        if _can_vectorise(obj):
            return np.asarray(obj)

        return np.array([as_array(el) if isinstance(el, (list, tuple, dict)) else el for el in obj], dtype=object)

    return obj


def as_list(obj: Any) -> Any:
    """Convert *obj* to a JSON-safe Python structure (lists, dicts, scalars)."""
    if obj is None:
        return obj
    
    if _is_numeric_scalar(obj):
        # Convert numpy scalars to Python scalars
        if isinstance(obj, np.generic):
            return obj.item()
        return obj
    
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    if isinstance(obj, np.generic):
        return obj.item()

    if isinstance(obj, dict):
        return {k: as_list(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [as_list(el) for el in obj]

    return obj


def encode_msgpack(obj: Any) -> bytes:
    """Encode *obj* into msgpack bytes, handling numpy arrays."""

    def default(o):
        if isinstance(o, np.ndarray):
            return {
                "__ndarray__": o.tobytes(),
                "dtype": str(o.dtype),
                "shape": o.shape,
            }
        if isinstance(o, np.generic):
            return {
                "__ndarray__": o.tobytes(),
                "dtype": str(o.dtype),
                "shape": (),
            }
        raise TypeError(f"Type not serializable: {type(o)}")

    return msgpack.packb(obj, default=default, use_bin_type=True)


def decode_msgpack(data: bytes) -> Any:
    """Decode msgpack *data*, reconstructing numpy arrays."""

    def object_hook(o):
        if "__ndarray__" in o:
            arr = np.frombuffer(o["__ndarray__"], dtype=np.dtype(o["dtype"]))
            shape = o.get("shape", ())
            return arr.reshape(shape)
        return o

    return msgpack.unpackb(data, object_hook=object_hook, raw=False)