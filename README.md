# telethon_objects_serialization
A working approach to serialize Telethon objects to strings

# Preface

The most annoying thing about developing with the Telethon library is the lack of object type information in the results of calling the to_dict() and stringify() methods.
The commonly used "Message" class name can belong to one of three classes (telethon.tl.custom.message.Message, telethon.tl.patched.Message, telethon.tl.types.Message). This means that every to_dict()/stringify() call must be accompanied by custom code logging the fully qualified class name of the object.
This also makes it impossible to reconstruct an object from its textual representation.

# Solution

Make the to_dict() method write the full class names by the key `"_"`.

# How

At the start of the application, patch the to_dict() method of all Telethon classes inherited from TLObject.

# Pros

Debugging and maintaining applications will become easier, and it will be possible to restore a class instance from a string created by calling the to_dict() method.

# Cons

- The class names returned by the stringify() method will also be fully qualified. Perhaps this should have been added to the "Pros" section.

- Recovering objects from a string may fail if different versions of Telethon are used for string conversion and vice versa. This is primarily due to different API versions (`telethon.tl.alltlobjects.LAYER` value).

# Code

`telethon_serialization.py`

Running `telethon_serialization.py` as script will check serialization on sample Message.

## Main code

`patch_telethon_classes()` patches to_dict() method of all TLObject's descendants.

`tl_obj_to_string()` converts Telethon object to string.

`tl_obj_from_string()` restores Telethon object from string.


## Other code

`report_same_basename_classes()` - report class names duplicates

`check_telethon_obj_serialization()` - converts passed object to string and back then compare result with source object.

