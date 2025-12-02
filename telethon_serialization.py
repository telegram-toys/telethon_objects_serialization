#!/usr/bin/env python3
"""
A working approach to serialize Telethon objects to strings
https://github.com/telegram-toys/telethon_objects_serialization
"""
import base64
import datetime
import json
import logging
import sys
import types
from typing import Any
from typing import Dict
from typing import Final
from typing import List
from typing import Optional
from typing import Set
from typing import Type

import telethon
from telethon.tl import TLObject
from telethon.tl import alltlobjects
from telethon.tl import patched
from telethon.tl.types import Message

logger = logging.getLogger(__name__)

_PATCHED_CLASS_NAMES: Final[Set[str]] = set()
_CLASS_CACHE: Final[Dict[str, Type[TLObject]]] = {}
_PATCH_CALLED: bool = False


def _check_patch_was_applied() -> None:
    if not _PATCH_CALLED:
        raise RuntimeError('No patched classes found. Did you forgot to call patch_telethon_classes()?')


def full_class_name(obj: Any) -> str:
    return f'{obj.__module__}.{obj.__qualname__}'


def _patch_to_dict_method(klass: Any) -> None:
    full_name = full_class_name(klass)

    if not issubclass(klass, TLObject):
        logger.warning('not a subclass of TLObject: %s -- %s', type(klass), full_name)
        return

    if full_name in _PATCHED_CLASS_NAMES:
        return
    _PATCHED_CLASS_NAMES.add(full_name)

    basename = klass.__qualname__

    original_func = klass.to_dict

    def new_to_dict(self: Type[TLObject]) -> Dict[str, Any]:
        result = original_func(self)
        if result['_'] != basename:
            raise ValueError(f'class name mismatch: dump={result['_']!r}, class={basename!r}')
        result['_'] = full_name
        return result

    klass.to_dict = new_to_dict

    _CLASS_CACHE[full_name] = klass

    logger.debug('patched %s', full_name)


def patch_telethon_classes() -> None:
    global _PATCH_CALLED
    if _PATCH_CALLED:
        raise RuntimeError('patch_telethon_classes already called')
    _PATCH_CALLED = True

    for klass in alltlobjects.tlobjects.values():
        _patch_to_dict_method(klass)
    alltlobjects_patched_count = len(_PATCHED_CLASS_NAMES)

    for subclass in TLObject.__subclasses__():
        _patch_to_dict_method(subclass)

    total_patched = len(_PATCHED_CLASS_NAMES)
    non_alltlobjects_patched_count = total_patched - alltlobjects_patched_count

    logger.info('Telethon version: %s, LAYER=%d', telethon.__version__, alltlobjects.LAYER)
    logger.info(
        'total classes patched: %d. alltlobjects: %d, non-alltlobjects: %d',
        total_patched, alltlobjects_patched_count, non_alltlobjects_patched_count,
    )


def report_same_basename_classes() -> None:
    _check_patch_was_applied()
    basename_stats: Dict[str, List[str]] = {}
    for full_name in _PATCHED_CLASS_NAMES:
        basename = full_name.split('.')[-1]
        basename_stats.setdefault(basename, list()).append(full_name)
    duplicate_count = 0
    for basename, full_names in sorted(basename_stats.items(), key=lambda x: x[0]):
        if len(full_names) < 2:
            continue
        duplicate_count += 1
        logger.info('%s [%d]: %s', basename, len(full_names), ', '.join(sorted(full_names)))
    logger.info('duplicate class names: %d', duplicate_count)


def get_telethon_class(class_name: str) -> Type[TLObject]:
    _check_patch_was_applied()
    if class_name in _CLASS_CACHE:
        return _CLASS_CACHE[class_name]

    raise ValueError(f'unknown class: {class_name}')


def restore_instance(raw: Any) -> Any:
    if isinstance(raw, (int, float, str, bytes, datetime.datetime, types.NoneType)):
        return raw
    elif isinstance(raw, list):
        return [restore_instance(x) for x in raw]
    elif isinstance(raw, dict):
        restored_dict = {k: restore_instance(v) for k, v in raw.items()}
        class_name = restored_dict.pop('_', None)
        if class_name is None:
            return restored_dict
        if not isinstance(class_name, str):
            raise ValueError(f'value for "_" key should be str but got {type(class_name)} -- {class_name!r}')
        obj_class = get_telethon_class(class_name)
        result = obj_class(**restored_dict)
        return result
    else:
        raise TypeError(f'unsupported type: {type(raw)}')


def default_json_helper(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, datetime.datetime):
        # if obj.tzinfo is None:
        #     raise ValueError(f'passed datetime without timezone: {obj}')
        return {'_isoformat': obj.isoformat()}
    elif isinstance(obj, bytes):
        return {'_base64': True, 'encoded': base64.encodebytes(obj).decode()}
    raise TypeError(f'default_json_helper: Object of type {type(obj)!r} is not serializable')


def object_hook_json_helper(obj: dict) -> Any:
    _isoformat = obj.get('_isoformat')
    if _isoformat is not None:
        return datetime.datetime.fromisoformat(_isoformat)

    _base64 = obj.get('_base64')
    if _base64 is not None:
        return base64.decodebytes(obj['encoded'].encode())

    return obj


def tl_obj_to_string(obj: TLObject, ensure_ascii: bool = True, indent: Optional[int] = None) -> str:
    _check_patch_was_applied()
    obj_dict = obj.to_dict()
    json_dump_str = json.dumps(obj_dict, ensure_ascii=ensure_ascii, indent=indent, default=default_json_helper)
    return json_dump_str


def tl_obj_from_string(dump: str) -> TLObject:
    _check_patch_was_applied()
    restored_dict = json.loads(dump, object_hook=object_hook_json_helper)
    restored_obj = restore_instance(restored_dict)
    if not isinstance(restored_obj, TLObject):
        raise TypeError(f'restored object is not descendant of TLObject but {type(restored_obj)!r}')
    return restored_obj


def make_test_message() -> TLObject:
    return patched.Message(
        id=1001,
        peer_id=telethon.tl.types.PeerChannel(
            channel_id=1002
        ),
        date=datetime.datetime(2025, 12, 1, 1, 2, 3, tzinfo=datetime.timezone.utc),
        message='message',
        out=False,
        mentioned=False,
        media_unread=False,
        silent=False,
        post=True,
        from_scheduled=False,
        legacy=False,
        edit_hide=True,
        pinned=False,
        noforwards=False,
        invert_media=False,
        offline=False,
        video_processing_pending=False,
        paid_suggested_post_stars=False,
        paid_suggested_post_ton=False,
        from_id=None,
        from_boosts_applied=None,
        saved_peer_id=None,
        fwd_from=telethon.tl.types.MessageFwdHeader(
            date=datetime.datetime(2025, 12, 1, 0, 1, 2, tzinfo=datetime.timezone.utc),
            imported=False,
            saved_out=False,
            from_id=telethon.tl.types.PeerChannel(
                channel_id=1003
            ),
            from_name=None,
            channel_post=1004,
            post_author=None,
            saved_from_peer=None,
            saved_from_msg_id=None,
            saved_from_id=None,
            saved_from_name=None,
            saved_date=None,
            psa_type=None
        ),
        via_bot_id=None,
        via_business_bot_id=None,
        reply_to=None,
        media=telethon.tl.types.MessageMediaPhoto(
            spoiler=False,
            photo=telethon.tl.types.Photo(
                id=1005,
                access_hash=1006,
                file_reference=b'\x02@\xd5\xff',
                date=datetime.datetime(2025, 12, 1, 1, 2, 3, tzinfo=datetime.timezone.utc),
                sizes=[
                    telethon.tl.types.PhotoStrippedSize(
                        type='i',
                        bytes=b'\x01\x15(b8\x89'
                    ),
                    telethon.tl.types.PhotoSize(
                        type='m',
                        w=320,
                        h=100,
                        size=1000
                    ),
                    telethon.tl.types.PhotoSize(
                        type='x',
                        w=800,
                        h=400,
                        size=2000
                    ),
                    telethon.tl.types.PhotoSizeProgressive(
                        type='y',
                        w=1080,
                        h=500,
                        sizes=[
                            10000,
                            20000,
                            40000,
                            50000,
                            70000,
                        ]
                    ),
                ],
                dc_id=100,
                has_stickers=False,
                video_sizes=[
                ]
            ),
            ttl_seconds=None
        ),
        reply_markup=None,
        entities=[
            # wrong ofsets just to show entities in message
            telethon.tl.types.MessageEntityTextUrl(
                offset=1,
                length=9,
                url='URL'
            ),
            telethon.tl.types.MessageEntityMention(
                offset=5,
                length=2
            ),
        ],
        views=100,
        forwards=10,
        replies=None,
        edit_date=datetime.datetime(2025, 12, 1, 1, 2, 4, tzinfo=datetime.timezone.utc),
        post_author=None,
        grouped_id=None,
        reactions=telethon.tl.types.MessageReactions(
            results=[
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='🤔'
                    ),
                    count=1,
                    chosen_order=None
                ),
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='❤'
                    ),
                    count=2,
                    chosen_order=None
                ),
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='👍'
                    ),
                    count=3,
                    chosen_order=None
                ),
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='😢'
                    ),
                    count=4,
                    chosen_order=None
                ),
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='👎'
                    ),
                    count=5,
                    chosen_order=None
                ),
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='🔥'
                    ),
                    count=6,
                    chosen_order=None
                ),
                telethon.tl.types.ReactionCount(
                    reaction=telethon.tl.types.ReactionEmoji(
                        emoticon='🤬'
                    ),
                    count=7,
                    chosen_order=None
                ),
            ],
            min=False,
            can_see_list=False,
            reactions_as_tags=False,
            recent_reactions=[
            ],
            top_reactors=[
            ]
        ),
        restriction_reason=[
        ],
        ttl_period=None,
        quick_reply_shortcut_id=None,
        effect=None,
        factcheck=None,
        report_delivery_until_date=None,
        paid_message_stars=None,
        suggested_post=None
    )


def check_telethon_obj_serialization(obj: TLObject) -> bool:
    # noinspection PyBroadException
    try:
        logger.debug('instance to test:\n%s', obj.stringify())
        obj_dump = tl_obj_to_string(obj, ensure_ascii=False)
        restored_obj = tl_obj_from_string(obj_dump)

        if not isinstance(restored_obj, obj.__class__):
            logger.error(
                'check_telethon_obj_serialization: class mismatch: was %s, restored %s',
                full_class_name(obj),
                full_class_name(restored_obj),
            )
            return False

        if obj.to_dict() == restored_obj.to_dict():
            logger.info('check_telethon_obj_serialization: OK')
            return True
        else:
            logger.error('check_telethon_obj_serialization: dumps are differ')
            logger.error('check_telethon_obj_serialization: source message dump:\n%s', obj.stringify())
            logger.error('check_telethon_obj_serialization: restored message dump:\n%s', restored_obj.stringify())
            return False

    except Exception:
        logger.exception('check_telethon_obj_serialization')
        logger.info('check_telethon_obj_serialization: trouble message:\n%s', obj.stringify())
        return False


def main() -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    patch_telethon_classes()
    report_same_basename_classes()

    check_telethon_obj_serialization(make_test_message())


if __name__ == '__main__':
    main()
