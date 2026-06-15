# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Avi
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

import asyncio

from pyrogram import enums, errors, filters, types

from Elevenyts import app, config, db, lang
from Elevenyts.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    """Handle /help command in private chats - shows help menu with image."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    try:
        await m.reply_photo(
            photo=config.START_IMG,  # Use same image as start command
            caption=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )
    except Exception:
        # Fallback to text if photo fails
        await m.reply_text(
            text=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    """
    Handle /start command - advanced welcome sequence for Monkey‑D Luffy.
    - Reacts with ❤️ to the start message.
    - Shows animated text messages (Monkey D Luffy → Welcome → Join my crew).
    - Sends sticker for 3 seconds.
    - Then sends main welcome picture with buttons.
    """
    # Auto-delete command message in group chats
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass
    
    # Skip if message from channel or anonymous admin
    if not message.from_user:
        return

    # Check if user is blacklisted
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    # React with ❤️ to the user's start command
    try:
        await message.react(emoji="❤️")
    except Exception:
        pass  # Ignore if reaction fails (older client or no permission)

    # If /start help, show help menu
    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    # Determine if chat is private or group
    private = message.chat.type == enums.ChatType.PRIVATE

    # ========== ADVANCED PRIVATE CHAT START SEQUENCE ==========
    if private:
        # 1. Animated text sequence (edit one message for smooth effect)
        # Send the first text
        anim_msg = await message.reply_text("⚡ Monkey D Luffy")
        await asyncio.sleep(0.8)

        # Edit to second text
        await anim_msg.edit_text("🌊 Welcome aboard!")
        await asyncio.sleep(0.8)

        # Edit to third text
        await anim_msg.edit_text("🏴‍☠️ Join my crew!")
        await asyncio.sleep(1.0)

        # Delete the animation message
        await anim_msg.delete()

        # 2. Send the sticker and keep it for 3 seconds
        sticker_id = "CAACAgIAAxkBAAERY5BqLmEBxz9fh5wcpacN1fIEpwdEtwACPUcAAisAAUFK1dzLvSrysQk8BA"
        sticker_msg = await message.reply_sticker(sticker_id)
        await asyncio.sleep(3)
        await sticker_msg.delete()

        # 3. Send the main welcome picture with caption and buttons
        _text = message.lang["start_pm"].format(
            message.from_user.first_name, "Monkey‑D Luffy"
        )
        key = buttons.start_key(message.lang, private=True)
        main_img = "https://files.catbox.moe/d580rf.jpeg"

        try:
            await message.reply_photo(
                photo=main_img,
                caption=_text,
                reply_markup=key,
                quote=True,
            )
        except errors.ChatSendPhotosForbidden:
            await message.reply_text(
                text=_text,
                reply_markup=key,
                quote=True,
            )

        # 4. Database and logging (behind the scenes)
        if not await db.is_user(message.from_user.id):
            await utils.send_log(message)
            await db.add_user(message.from_user.id)

        return

    # ========== GROUP CHAT START (unchanged) ==========
    # If not private, it's a group start – use old welcome
    _text = message.lang["start_gp"].format(app.name)
    key = buttons.start_key(message.lang, private=False)

    try:
        await message.reply_photo(
            photo=config.START_IMG,
            caption=_text,
            reply_markup=key,
            quote=not private,
        )
    except errors.ChatSendPhotosForbidden:
        await message.reply_text(
            text=_text,
            reply_markup=key,
            quote=not private,
        )


# ========== Other commands unchanged ==========
@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    """Handle /playmode or /settings command - show group settings."""
    try:
        await message.delete()
    except Exception:
        pass
    
    admin_only = await db.get_play_mode(message.chat.id)
    _language = "en"
    await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    """Handle new member events - detect when bot is added to groups."""
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await db.add_chat(message.chat.id)
