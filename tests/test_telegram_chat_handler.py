import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Message, Update, PhotoSize, Video
from telegram.ext import ContextTypes

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from bot.handlers.telegram_chat_handler import UserMessage


@pytest.mark.asyncio
async def test_handle_text_message():
    # Arrange
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 12345
    name = "Tester"
    reply_to_id = 6789
    text = "Hello, world!"
    update.message.text = text

    # Mock bot's send_message method
    context.bot.send_message = AsyncMock(return_value="sent-message")

    # Act
    result = await handler._handle_text_message(
        update, context, partner_id, name, reply_to_id, secret_chat=False
    )

    # Assert
    context.bot.send_message.assert_awaited_once_with(
        partner_id,
        f"{name}: {text}",
        reply_to_message_id=reply_to_id,
    )
    assert result == "sent-message"


@pytest.mark.asyncio
async def test_handle_photo_message():
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 12345
    name = "Tester"
    reply_to_id = 6789
    caption = "A photo"
    photo_file_id = "photo123"
    update.message.caption = caption
    # Simulate the photo list with a PhotoSize object
    photo_mock = MagicMock(spec=PhotoSize)
    photo_mock.file_id = photo_file_id
    update.message.photo = [photo_mock]
    context.bot.send_photo = AsyncMock(return_value="sent-photo")

    result = await handler._handle_photo_message(
        update, context, partner_id, name, reply_to_id, secret_chat=True
    )

    context.bot.send_photo.assert_awaited_once_with(
        partner_id,
        photo=photo_file_id,
        caption=f"{name}: {caption}",
        reply_to_message_id=reply_to_id,
        has_spoiler=True,
        protect_content=True,
    )
    assert result == "sent-photo"


@pytest.mark.asyncio
async def test_handle_video_message():
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 12345
    name = "Tester"
    reply_to_id = 6789
    caption = "A video"
    video_file_id = "video123"
    update.message.caption = caption
    video_mock = MagicMock(spec=Video)
    video_mock.file_id = video_file_id
    update.message.video = video_mock
    context.bot.send_video = AsyncMock(return_value="sent-video")

    result = await handler._handle_video_message(
        update, context, partner_id, name, reply_to_id, secret_chat=True
    )

    context.bot.send_video.assert_awaited_once_with(
        partner_id,
        video=video_file_id,
        caption=f"{name}: {caption}",
        reply_to_message_id=reply_to_id,
        has_spoiler=True,
        protect_content=True,
        supports_streaming=True,
    )
    assert result == "sent-video"


# You can add similar tests for _handle_video_note_message and other public methods.


@pytest.mark.asyncio
async def test_handle_text_message_no_reply():
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 11111
    name = "NoReplyUser"
    reply_to_id = None
    update.message.text = "Just a msg"
    context.bot.send_message = AsyncMock(return_value="sent-message")
    result = await handler._handle_text_message(
        update, context, partner_id, name, reply_to_id, secret_chat=False
    )
    context.bot.send_message.assert_awaited_once_with(
        partner_id,
        f"{name}: {update.message.text}",
        reply_to_message_id=None,
    )
    assert result == "sent-message"


@pytest.mark.asyncio
async def test_handle_photo_message_no_caption():
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 22222
    name = "PhotoUser"
    reply_to_id = 9876
    # Simulate no caption, only photo
    update.message.caption = None
    photo_mock = MagicMock(spec=PhotoSize)
    photo_mock.file_id = "photo_no_caption"
    update.message.photo = [photo_mock]
    context.bot.send_photo = AsyncMock(return_value="sent-photo")
    result = await handler._handle_photo_message(
        update, context, partner_id, name, reply_to_id, secret_chat=False
    )
    context.bot.send_photo.assert_awaited_once_with(
        partner_id,
        photo="photo_no_caption",
        caption=None,
        reply_to_message_id=reply_to_id,
        has_spoiler=False,
        protect_content=False,
    )
    assert result == "sent-photo"


@pytest.mark.asyncio
async def test_handle_video_message_non_secret():
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 33333
    name = "VideoUser"
    reply_to_id = 1234
    update.message.caption = "Watch this"
    video_mock = MagicMock(spec=Video)
    video_mock.file_id = "video_file"
    update.message.video = video_mock
    context.bot.send_video = AsyncMock(return_value="sent-video")
    result = await handler._handle_video_message(
        update, context, partner_id, name, reply_to_id, secret_chat=False
    )
    context.bot.send_video.assert_awaited_once_with(
        partner_id,
        video="video_file",
        caption=f"{name}: Watch this",
        reply_to_message_id=reply_to_id,
        has_spoiler=False,
        protect_content=False,
        supports_streaming=False,
    )
    assert result == "sent-video"


@pytest.mark.asyncio
async def test_get_reply_to_id_none():
    handler = UserMessage()
    message = MagicMock(spec=Message)
    message.reply_to_message = None
    assert handler._get_reply_to_id(message) is None


def test_get_reply_to_id_calls_db_methods(monkeypatch):
    handler = UserMessage()
    message = MagicMock(spec=Message)
    reply_message = MagicMock()
    reply_message.message_id = 555
    message.reply_to_message = reply_message

    # Patch database methods
    monkeypatch.setattr(handler.db, "get_msg_id_by_robot_msg", lambda msg_id: None)
    monkeypatch.setattr(handler.db, "get_msg_id_by_user_msg", lambda msg_id: 42)
    assert handler._get_reply_to_id(message) == 42


@pytest.mark.asyncio
async def test_handle_photo_message_with_spoiler_and_protect():
    handler = UserMessage()
    update = MagicMock(spec=Update)
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    partner_id = 44444
    name = "SecretPhotoUser"
    reply_to_id = 9999
    caption = "Secret pic"
    photo_file_id = "secret_photo"
    update.message.caption = caption
    photo_mock = MagicMock(spec=PhotoSize)
    photo_mock.file_id = photo_file_id
    update.message.photo = [photo_mock]
    context.bot.send_photo = AsyncMock(return_value="sent-photo")
    result = await handler._handle_photo_message(
        update, context, partner_id, name, reply_to_id, secret_chat=True
    )
    context.bot.send_photo.assert_awaited_once_with(
        partner_id,
        photo=photo_file_id,
        caption=f"{name}: {caption}",
        reply_to_message_id=reply_to_id,
        has_spoiler=True,
        protect_content=True,
    )
    assert result == "sent-photo"
