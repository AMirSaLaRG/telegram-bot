# Database Schema Documentation

This document outlines the database schema used in the application, defined in `data_base.py`. The database is a SQLite database located at `database/telegram_database.db`.

## Table of Contents
1.  [Users Table (`users`)](#users-table-users)
2.  [Gold & Dollar Rial Table (`gold`)](#gold--dollar-rial-table-gold)
3.  [Torob Item Table (`torob_item`)](#torob-item-table-torob-item)
4.  [Torob Check Table (`torob_check`)](#torob-check-table-torob-check)
5.  [User Sessions Table (`users_sessions`)](#user-sessions-table-users_sessions)
6.  [Message Map Table (`message_map`)](#message-map-table-message_map)
7.  [Links Table (`links`)](#links-table-links)

---

## 1. Users Table (`users`)
This table stores information about the users of the application.

| Column Name     | Type      | Attributes                  | Description                                |
| :-------------- | :-------- | :-------------------------- | :----------------------------------------- |
| `user_id`       | `Integer` | Primary Key                 | Unique identifier for the user.            |
| `generated_id`  | `String`  |                             | A securely generated unique ID for the user. |
| `name`          | `String(50)` | Nullable                  | User's full name.                            |
| `first_name`    | `String(50)` | Nullable                  | User's first name.                         |
| `last_name`     | `String(50)` | Nullable                  | User's last name.                          |
| `gender`        | `String(50)` | Nullable                  | User's gender.                             |
| `age`           | `Integer` | Nullable                  | User's age.                                |
| `city`          | `String(50)` | Nullable                  | User's city.                               |
| `last_online`   | `DateTime` | Default: `datetime.now`   | Timestamp of the user's last online activity. |
| `profile_photo` | `Text`    | Nullable                  | URL or path to the user's profile photo. |
| `about`         | `Text`    | Default: `'No bio yet'`   | User's "about me" description.             |
| `latitude`      | `Float`   | Nullable                  | Latitude of the user's location.           |
| `longitude`     | `Float`   | Nullable                  | Longitude of the user's location.          |
| `registration_date` | `DateTime` | Default: `datetime.now` | Date and time when the user registered.      |

## 2. Gold & Dollar Rial Table (`gold`)
This table stores historical data for gold and dollar prices in Rial and USD.

| Column Name                       | Type       | Attributes    | Description                                            |
| :-------------------------------- | :--------- | :------------ | :----------------------------------------------------- |
| `check_id`                        | `Integer`  | Primary Key   | Unique identifier for each price check entry. |
| `gold_18k_ir`                     | `Float`    | Not Nullable  | Price of 18K gold in Iranian Rial.           |
| `dollar_ir_rial`                  | `Float`    | Not Nullable  | Price of US Dollar in Iranian Rial.         |
| `time_check_ir`                   | `DateTime` | Not Nullable  | Timestamp of the Iranian gold/dollar price check. |
| `gold_18k_international_dollar`   | `Float`    | Not Nullable  | International price of 18K gold in USD.      |
| `gold_18k_international_rial`     | `Float`    | Not Nullable  | International price of 18K gold converted to Rial. |
| `time_check_int`                  | `DateTime` | Not Nullable  | Timestamp of the international gold price check. |

## 3. Torob Item Table (`torob_item`)
This table stores items that users are tracking prices for from Torob (a price comparison website).

| Column Name          | Type       | Attributes                       | Description                                       |
| :------------------- | :--------- | :------------------------------- | :------------------------------------------------ |
| `item_id`            | `Integer`  | Primary Key                      | Unique identifier for the tracked item.   |
| `user_id`            | `Integer`  | Not Nullable                     | The ID of the user who added this item.     |
| `name_of_item`       | `String`   | Not Nullable                     | Name or description of the item.          |
| `user_preferred_price` | `Float`    | Not Nullable                     | The price the user prefers for this item. |
| `torob_url`          | `String`   | Not Nullable                     | The URL of the item on Torob.             |
| `created_at`         | `DateTime` | Default: `func.now()`            | Timestamp when the item was added.        |
| `updated_at`         | `DateTime` | On Update: `func.now()`          | Timestamp of the last update to the item. |

**Relationships:**
* `price_checks`: One-to-Many relationship with `TorobCheck` (an item can have many price checks).

## 4. Torob Check Table (`torob_check`)
This table records the historical price checks for items tracked in the `torob_item` table.

| Column Name       | Type       | Attributes                   | Description                                  |
| :---------------- | :--------- | :--------------------------- | :------------------------------------------- |
| `check_id`        | `Integer`  | Primary Key                  | Unique identifier for each price check. |
| `item_id`         | `Integer`  | Foreign Key (`torob_item.item_id`) | The ID of the item being checked.      |
| `checked_price`   | `Float`    | Not Nullable                 | The price recorded during this check. |
| `check_timestamp` | `DateTime` | Default: `func.now()`        | Timestamp when the price check occurred. |

**Relationships:**
* `item`: Many-to-One relationship with `TorobScrapUser` (many checks belong to one item).

## 5. User Sessions Table (`users_sessions`)
This table manages user session information, particularly for chat functionalities.

| Column Name          | Type       | Attributes                       | Description                                            |
| :------------------- | :--------- | :------------------------------- | :----------------------------------------------------- |
| `user_id`            | `Integer`  | Primary Key, Foreign Key (`users.user_id`) | Unique identifier for the user, linked to the `users` table. |
| `partner_id`         | `Integer`  | Nullable                         | The ID of the user currently chatting with. |
| `perv_partner_id`    | `Integer`  | Nullable                         | The ID of the previous chat partner.        |
| `secret_chat`        | `Boolean`  | Default: `False`                 | Indicates if the current chat is a secret chat. |
| `created_at`         | `DateTime` | Default: `func.now()`            | Timestamp when the session was created.    |
| `updated_at`         | `DateTime` | On Update: `func.now()`          | Timestamp of the last update to the session. |
| `looking_random_chat` | `Boolean`  | Default: `False`                 | Indicates if the user is looking for a random chat. |

**Indexes:**
* `idx_partner`: Index on `partner_id` for efficient lookup of partners.

**Relationships:**
* `sent_messages`: One-to-Many relationship with `MessageMap` (messages sent by this user).
* `received_messages`: One-to-Many relationship with `MessageMap` (messages received by this user).
* `links`: One-to-Many relationship with `Links` (links owned by this user).

## 6. Message Map Table (`message_map`)
This table maps messages between users, storing details about each message.

| Column Name     | Type       | Attributes                       | Description                                   |
| :-------------- | :--------- | :------------------------------- | :-------------------------------------------- |
| `message_id`    | `Integer`  | Primary Key                      | Unique identifier for each message.   |
| `bot_message_id` | `Integer`  | Not Nullable                     | The message ID from the bot's perspective. |
| `sender_id`     | `Integer`  | Foreign Key (`users_sessions.user_id`), Not Nullable | The ID of the user who sent the message. |
| `receiver_id`   | `Integer`  | Foreign Key (`users_sessions.user_id`), Not Nullable | The ID of the user who received the message. |
| `time`          | `DateTime` | Nullable                         | The time the message was sent.      |
| `created_at`    | `DateTime` | Default: `func.now()`            | Timestamp when the message record was created. |
| `updated_at`    | `DateTime` | On Update: `func.now()`          | Timestamp of the last update to the message record. |
| `msg_txt`       | `String`   | Nullable                         | The text content of the message.    |
| `requested`     | `Boolean`  | Nullable                         | Indicates if the message was a request. |

**Indexes:**
* `idx_conversation`: Composite index on `sender_id` and `receiver_id` for conversation lookup.
* `idx_conversation_reverse`: Reverse composite index on `receiver_id` and `sender_id` for conversation lookup.
* `idx_message_time`: Index on `time` for time-based message queries.
* `idx_bot_message`: Index on `bot_message_id` for tracking bot messages.

**Relationships:**
* `sender`: Many-to-One relationship with `Sessions` (the sender of the message).
* `receiver`: Many-to-One relationship with `Sessions` (the receiver of the message).

## 7. Links Table (`links`)
This table stores information about generated links, such as anonymous chat links.

| Column Name     | Type       | Attributes                       | Description                                   |
| :-------------- | :--------- | :------------------------------- | :-------------------------------------------- |
| `id`            | `Integer`  | Primary Key                      | Unique identifier for the link.       |
| `link`          | `String`   | Unique                           | The unique generated link string.     |
| `expire_time`   | `DateTime` | Not Nullable                     | The expiration time of the link.    |
| `owner_id`      | `Integer`  | Foreign Key (`users_sessions.user_id`) | The ID of the user who owns this link. |
| `max_uses`      | `Integer`  | Nullable                         | The maximum number of times the link can be used. |
| `number_of_used` | `Integer`  | Default: `0`, Nullable           | The current number of times the link has been used. |
| `active`        | `Boolean`  | Default: `True`, Not Nullable    | Indicates if the link is active.    |
| `created_at`    | `DateTime` | Default: `func.now()`            | Timestamp when the link was created. |

**Indexes:**
* `idx_link_active`: Index on `link` and `active` for filtering active links.
* `idx_owner_link`: Index on `owner_id` and `link` for lookup by owner and link.

**Relationships:**
* `owner`: Many-to-One relationship with `Sessions` (the owner of the link).