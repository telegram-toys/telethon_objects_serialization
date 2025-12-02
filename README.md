# telethon_objects_serialization
A working approach to serialize Telethon objects to strings and back.

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

<details>
  <summary>Sample output</summary>

```
Telethon version: 1.42.0, LAYER=216
total classes patched: 2281. alltlobjects: 2272, non-alltlobjects: 9
Authorization [2]: telethon.tl.types.Authorization, telethon.tl.types.auth.Authorization
AutoDownloadSettings [2]: telethon.tl.types.AutoDownloadSettings, telethon.tl.types.account.AutoDownloadSettings
AutoSaveSettings [2]: telethon.tl.types.AutoSaveSettings, telethon.tl.types.account.AutoSaveSettings
BotApp [2]: telethon.tl.types.BotApp, telethon.tl.types.messages.BotApp
BotInfo [2]: telethon.tl.types.BotInfo, telethon.tl.types.bots.BotInfo
ChannelParticipant [2]: telethon.tl.types.ChannelParticipant, telethon.tl.types.channels.ChannelParticipant
ChatFull [2]: telethon.tl.types.ChatFull, telethon.tl.types.messages.ChatFull
CheckUsernameRequest [2]: telethon.tl.functions.account.CheckUsernameRequest, telethon.tl.functions.channels.CheckUsernameRequest
DeleteHistoryRequest [2]: telethon.tl.functions.channels.DeleteHistoryRequest, telethon.tl.functions.messages.DeleteHistoryRequest
DeleteMessagesRequest [2]: telethon.tl.functions.channels.DeleteMessagesRequest, telethon.tl.functions.messages.DeleteMessagesRequest
ExportedChatlistInvite [2]: telethon.tl.types.ExportedChatlistInvite, telethon.tl.types.chatlists.ExportedChatlistInvite
GetDifferenceRequest [2]: telethon.tl.functions.langpack.GetDifferenceRequest, telethon.tl.functions.updates.GetDifferenceRequest
GetMessagesRequest [2]: telethon.tl.functions.channels.GetMessagesRequest, telethon.tl.functions.messages.GetMessagesRequest
GroupCall [2]: telethon.tl.types.GroupCall, telethon.tl.types.phone.GroupCall
Message [3]: telethon.tl.custom.message.Message, telethon.tl.patched.Message, telethon.tl.types.Message
MessageEmpty [2]: telethon.tl.patched.MessageEmpty, telethon.tl.types.MessageEmpty
MessageService [2]: telethon.tl.patched.MessageService, telethon.tl.types.MessageService
MessageViews [2]: telethon.tl.types.MessageViews, telethon.tl.types.messages.MessageViews
PeerSettings [2]: telethon.tl.types.PeerSettings, telethon.tl.types.messages.PeerSettings
PeerStories [2]: telethon.tl.types.PeerStories, telethon.tl.types.stories.PeerStories
PhoneCall [2]: telethon.tl.types.PhoneCall, telethon.tl.types.phone.PhoneCall
Photo [2]: telethon.tl.types.Photo, telethon.tl.types.photos.Photo
ReadHistoryRequest [2]: telethon.tl.functions.channels.ReadHistoryRequest, telethon.tl.functions.messages.ReadHistoryRequest
ReadMessageContentsRequest [2]: telethon.tl.functions.channels.ReadMessageContentsRequest, telethon.tl.functions.messages.ReadMessageContentsRequest
ReorderUsernamesRequest [3]: telethon.tl.functions.account.ReorderUsernamesRequest, telethon.tl.functions.bots.ReorderUsernamesRequest, telethon.tl.functions.channels.ReorderUsernamesRequest
ReportRequest [2]: telethon.tl.functions.messages.ReportRequest, telethon.tl.functions.stories.ReportRequest
ReportSpamRequest [2]: telethon.tl.functions.channels.ReportSpamRequest, telethon.tl.functions.messages.ReportSpamRequest
SearchPostsRequest [2]: telethon.tl.functions.channels.SearchPostsRequest, telethon.tl.functions.stories.SearchPostsRequest
SearchRequest [2]: telethon.tl.functions.contacts.SearchRequest, telethon.tl.functions.messages.SearchRequest
SendReactionRequest [2]: telethon.tl.functions.messages.SendReactionRequest, telethon.tl.functions.stories.SendReactionRequest
SetMainProfileTabRequest [2]: telethon.tl.functions.account.SetMainProfileTabRequest, telethon.tl.functions.channels.SetMainProfileTabRequest
StickerSet [2]: telethon.tl.types.StickerSet, telethon.tl.types.messages.StickerSet
StoryViews [2]: telethon.tl.types.StoryViews, telethon.tl.types.stories.StoryViews
ToggleUsernameRequest [3]: telethon.tl.functions.account.ToggleUsernameRequest, telethon.tl.functions.bots.ToggleUsernameRequest, telethon.tl.functions.channels.ToggleUsernameRequest
UpdateColorRequest [2]: telethon.tl.functions.account.UpdateColorRequest, telethon.tl.functions.channels.UpdateColorRequest
UpdateEmojiStatusRequest [2]: telethon.tl.functions.account.UpdateEmojiStatusRequest, telethon.tl.functions.channels.UpdateEmojiStatusRequest
UpdateUsernameRequest [2]: telethon.tl.functions.account.UpdateUsernameRequest, telethon.tl.functions.channels.UpdateUsernameRequest
UserFull [2]: telethon.tl.types.UserFull, telethon.tl.types.users.UserFull
WebPage [2]: telethon.tl.types.WebPage, telethon.tl.types.messages.WebPage
duplicate class names: 39
check_telethon_obj_serialization: OK
```  
</details>

## Main code

`patch_telethon_classes()` patches to_dict() method of all TLObject's descendants.

`tl_obj_to_string()` converts Telethon object to string.

`tl_obj_from_string()` restores Telethon object from string.


## Other code

`report_same_basename_classes()` - report class names duplicates

`check_telethon_obj_serialization()` - converts passed object to string and back then compare result with source object.

