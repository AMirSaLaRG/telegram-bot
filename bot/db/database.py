import httpx
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    select,
    inspect,
    ForeignKey,
    Index,
    Boolean,
    text,
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from bot.service.dolar_gold_price_ir import CheckSitePrice
from typing import Optional, Type, List
from sqlalchemy.sql import func
import os
import secrets
import string
import logging

# Get the absolute path of the directory containing the current script
basedir = os.path.abspath(os.path.dirname(__file__))
# Construct the path to the SQLite database file
db_path = os.path.join(basedir, "database/telegram_database.db")
# Define the SQLAlchemy database URI
SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_path

# ___________________________Web scraping Class_____________________________________________
site_checker_gold = CheckSitePrice()

# Base class for declarative models
Base = declarative_base()


# ___________________________________________________________________________________________
def generate_secure_random_id(length=8):
    """
        Generates a secure, random ID string with a mix of lowercase, uppercase, and digits.

        Args:
            length (int): The desired length of the generated ID. Defaults to 8.
    ghg
        Returns:
            str: A randomly generated ID string.
    """
    # Define character sets for ID generation
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = ""  # No special characters currently used

    # Combine all allowed characters
    all_chars = lowercase + uppercase + digits + special

    # Ensure at least one character from each specified set (lowercase, uppercase, digits)
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        # secrets.choice(special) # Uncomment if special characters are desired
    ]

    # Fill the rest of the ID with random choices from all characters
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle the list to avoid predictable patterns and increase randomness
    secrets.SystemRandom().shuffle(password)

    # Convert the list of characters to a single string
    return "".join(password)


# Example usage (commented out, as per instruction not to change code)
# new_id = generate_secure_random_id()
# print(new_id)

# ___________________________________________________________________________________________
# _________________Initiate Users data base (for chat , etc, ..)_____________________________
# ___________________________________________________________________________________________


class User(Base):
    """
    SQLAlchemy model for storing user information.
    Represents the 'users' table in the database.
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    generated_id = Column(String)
    name = Column(String(50), nullable=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(50), nullable=True)
    last_online = Column(DateTime, default=datetime.now, nullable=True)
    profile_photo = Column(Text, nullable=True)
    about = Column(Text, default="No bio yet", nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    registration_date = Column(DateTime, default=datetime.now, nullable=True)
    language = Column(String, default="0")

    friends = relationship(
        "User",
        secondary="relationships",
        primaryjoin="and_(User.user_id==Relationships.user_id, Relationships.friend==True)",
        secondaryjoin="and_(User.user_id==Relationships.target_id, Relationships.friend==True)",
        backref="friend_of",
        viewonly=True,
    )

    likes = relationship(
        "User",
        secondary="relationships",
        primaryjoin="and_(User.user_id==Relationships.user_id, Relationships.like==True)",
        secondaryjoin="and_(User.user_id==Relationships.target_id, Relationships.like==True)",
        backref="liked_by",
        viewonly=True,
    )

    blocks = relationship(
        "User",
        secondary="relationships",
        primaryjoin="and_(User.user_id==Relationships.user_id, Relationships.block==True)",
        secondaryjoin="and_(User.user_id==Relationships.target_id, Relationships.block==True)",
        backref="blocked_by",
        viewonly=True,
    )

    reports = relationship(
        "User",
        secondary="relationships",
        primaryjoin="and_(User.user_id==Relationships.user_id, Relationships.report==True)",
        secondaryjoin="and_(User.user_id==Relationships.target_id, Relationships.report==True)",
        backref="reported_by",
        viewonly=True,
    )


class Relationships(Base):
    __tablename__ = "relationships"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    target_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    like = Column(Boolean, default=False)
    friend = Column(Boolean, default=False)
    block = Column(Boolean, default=False)
    report = Column(Boolean, default=False)


# ___________________________________________________________________________________________
# ____________________________Initiate Gold & Dollar data base ______________________________
# ___________________________________________________________________________________________


class GoldDollarRial(Base):
    """
    SQLAlchemy model for storing gold and dollar prices.
    Represents the 'gold' table in the database.
    """

    __tablename__ = "gold"

    check_id = Column(Integer, primary_key=True)
    gold_18k_ir = Column(Float, nullable=False)
    dollar_ir_rial = Column(Float, nullable=False)
    time_check_ir = Column(DateTime, nullable=False)
    gold_18k_international_dollar = Column(Float, nullable=False)
    gold_18k_international_rial = Column(Float, nullable=False)
    time_check_int = Column(DateTime, nullable=False)


# ___________________________________________________________________________________________
# ____________________________Initiate Torob Scraping data base ______________________________
# ___________________________________________________________________________________________


class TorobScrapUser(Base):
    """
    SQLAlchemy model for items a user wants to track on Torob.
    Represents the 'torob_item' table.
    """

    __tablename__ = "torob_item"

    item_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name_of_item = Column(String, nullable=False)
    user_preferred_price = Column(Float, nullable=False)
    torob_url = Column(String, nullable=False)
    created_at = Column(
        DateTime, server_default=func.now()
    )  # Database timestamp for creation
    updated_at = Column(
        DateTime, onupdate=func.now()
    )  # Database timestamp for last update
    # Relationship to TorobCheck: an item can have many price checks
    price_checks = relationship(
        "TorobCheck",
        back_populates="item",
        cascade="all, delete-orphan",  # Deletes associated checks when an item is deleted
    )


class TorobCheck(Base):
    """
    SQLAlchemy model for individual price checks of a Torob item.
    Represents the 'torob_check' table.
    """

    __tablename__ = "torob_check"

    check_id = Column(Integer, primary_key=True)
    item_id = Column(
        Integer, ForeignKey("torob_item.item_id")
    )  # Foreign key linking to TorobScrapUser
    checked_price = Column(Float, nullable=False)
    check_timestamp = Column(
        DateTime, server_default=func.now()
    )  # Timestamp of when the check occurred

    # Relationship back to TorobScrapUser: a check belongs to one item
    item = relationship("TorobScrapUser", back_populates="price_checks")


# ___________________________________________________________________________________________
# _____________________________Initiate Users Chat data base ________________________________
# ___________________________________________________________________________________________


class Sessions(Base):
    """
    SQLAlchemy model for managing user chat sessions and relationships.
    Represents the 'users_sessions' table.
    """

    __tablename__ = "users_sessions"

    user_id = Column(
        Integer, ForeignKey("users.user_id"), primary_key=True
    )  # Foreign key to User table

    partner_id = Column(Integer, nullable=True)
    perv_partner_id = Column(Integer, nullable=True)  # Previous partner ID
    secret_chat = Column(Boolean, default=False)
    created_at = Column(
        DateTime, server_default=func.now()
    )  # Timestamp for session creation
    updated_at = Column(
        DateTime, onupdate=func.now()
    )  # Timestamp for last session update
    looking_random_chat = Column(Boolean, default=False)

    # Relationship to messages where this user is the sender
    sent_messages = relationship(
        "MessageMap", foreign_keys="[MessageMap.sender_id]", back_populates="sender"
    )
    # Relationship to messages where this user is the receiver
    received_messages = relationship(
        "MessageMap", foreign_keys="[MessageMap.receiver_id]", back_populates="receiver"
    )
    # Relationship to Links owned by this user
    links = relationship(
        "Links", foreign_keys="[Links.owner_id]", back_populates="owner"
    )
    # Table arguments, including an index for partner_id for faster lookups
    __table_args__ = (Index("idx_partner", "partner_id"),)


# ___________________________________________________________________________________________
# _____________________________Initiate Users Message Map data base ________________________________
# ___________________________________________________________________________________________


class MessageMap(Base):
    """
    SQLAlchemy model for mapping messages between users through the bot.
    Represents the 'message_map' table.
    """

    __tablename__ = "message_map"

    message_id = Column(Integer, primary_key=True)  # User's internal message ID
    bot_message_id = Column(
        Integer, nullable=False
    )  # Bot's message ID (e.g., from Telegram API)
    sender_id = Column(Integer, ForeignKey("users_sessions.user_id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users_sessions.user_id"), nullable=False)
    time = Column(DateTime, nullable=True)  # Timestamp of the message
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    msg_txt = Column(String, nullable=True)  # Text content of the message
    requested = Column(Boolean, nullable=True)  # Flag for requested messages

    # Relationship to the sender (Sessions)
    sender = relationship(
        "Sessions", foreign_keys=[sender_id], back_populates="sent_messages"
    )
    # Relationship to the receiver (Sessions)
    receiver = relationship(
        "Sessions", foreign_keys=[receiver_id], back_populates="received_messages"
    )

    # Recommended indexes for efficient queries
    __table_args__ = (
        # Composite index for finding conversations between two users
        Index("idx_conversation", "sender_id", "receiver_id"),
        # Reverse composite index for the same conversation (for dual-direction lookup)
        Index("idx_conversation_reverse", "receiver_id", "sender_id"),
        # Index for time-based queries (e.g., retrieving message history)
        Index("idx_message_time", "time"),
        # Index for bot message tracking (if querying by bot_message_id)
        Index("idx_bot_message", "bot_message_id"),
    )


# ___________________________________________________________________________________________
# _____________________________Initiate Users Links data base ________________________________
# ___________________________________________________________________________________________


class Links(Base):
    """
    SQLAlchemy model for managing unique links or tokens, possibly for invites or special access.
    Represents the 'links' table.
    """

    __tablename__ = "links"

    id = Column(Integer, primary_key=True)
    link = Column(String, unique=True)  # The unique link/token string
    expire_time = Column(DateTime, nullable=False)
    owner_id = Column(
        Integer, ForeignKey("users_sessions.user_id")
    )  # Owner of the link
    max_uses = Column(
        Integer, nullable=True
    )  # Maximum number of times the link can be used
    number_of_used = Column(
        Integer, nullable=True, default=0
    )  # Counter for how many times the link has been used
    active = Column(
        Boolean, default=True, nullable=False
    )  # Flag to indicate if the link is active
    created_at = Column(
        DateTime, server_default=func.now()
    )  # Timestamp for link creation

    # Relationship back to owner (Sessions)
    owner = relationship(
        "Sessions",
        back_populates="links",  # Matches Sessions.links
        foreign_keys=[owner_id],
    )
    # Indexes for efficient link lookup
    __table_args__ = (
        Index("idx_link_active", "link", "active"),  # For quick lookup of active links
        Index("idx_owner_link", "owner_id", "link"),  # For finding links by owner
    )


class RelationshipManager:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_or_create_relationship(
        self, session, user_id: int, target_id: int
    ) -> Relationships:
        """Helper method to get or create a relationship record"""

        the_relationship = (
            session.query(Relationships)
            .filter(
                Relationships.user_id == user_id,  # Fixed filter syntax
                Relationships.target_id == target_id,
            )
            .first()
        )

        if not the_relationship:
            the_relationship = Relationships(
                user_id=user_id,
                target_id=target_id,
                like=False,
                friend=False,
                block=False,
                report=False,
            )
            session.add(the_relationship)
        return the_relationship

    def block(self, user_id: int, target_id: int, action=True) -> bool:
        with self.Session() as session:
            try:
                the_relationship = self._get_or_create_relationship(
                    session, user_id, target_id
                )
                the_relationship.like = False
                the_relationship.friend = False
                the_relationship.block = action

                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                print(f"Invalid user IDs: {user_id} or {target_id}")
                return False
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Database error blocking user: {e}")
                return False

    def friend(self, user_id: int, target_id: int, action=True) -> bool:
        with self.Session() as session:
            try:
                the_relationship = self._get_or_create_relationship(
                    session, user_id, target_id
                )
                the_relationship.friend = action
                if action:
                    the_relationship.block = False

                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                print(f"Invalid user IDs: {user_id} or {target_id}")
                return False
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Database error while friending user: {e}")
                return False

    def like(self, user_id: int, target_id: int, action=True) -> bool:
        with self.Session() as session:
            try:
                the_relationship = self._get_or_create_relationship(
                    session, user_id, target_id
                )
                the_relationship.like = action
                if action:
                    the_relationship.block = False

                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                print(f"Invalid user IDs: {user_id} or {target_id}")
                return False
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Database error while liking user: {e}")
                return False

    def report(self, user_id: int, target_id: int, action=True) -> bool:
        with self.Session() as session:
            try:
                the_relationship = self._get_or_create_relationship(
                    session, user_id, target_id
                )

                the_relationship.report = action

                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                print(f"Invalid user IDs: {user_id} or {target_id}")
                return False
            except SQLAlchemyError as e:
                session.rollback()
                print(f"Database error while reporting user: {e}")
                return False

    def get_relationship_status(self, user_id: int, target_id: int) -> dict:
        """Get complete relationship status between two users"""
        with self.Session() as session:
            try:
                rel = (
                    session.query(Relationships)
                    .filter(
                        Relationships.user_id == user_id,
                        Relationships.target_id == target_id,
                    )
                    .first()
                )

                if not rel:
                    return {
                        "like": False,
                        "friend": False,
                        "block": False,
                        "report": False,
                    }

                return {
                    "like": rel.like,
                    "friend": rel.friend,
                    "block": rel.block,
                    "report": rel.report,
                }
            except SQLAlchemyError as e:
                print(f"Error getting relationship status: {e}")
                return {}

    def get_user_relationships(self, user_id: int) -> dict:
        """Get all relationship data for a user in both directions returns User objects"""
        with self.Session() as session:
            try:
                user = session.query(User).get(user_id)
                if not user:
                    return {}

                # Initialize result structure
                result = {
                    "friends": user.friends,
                    "friend_of": user.friend_of,
                    "likes": user.likes,
                    "liked_by": user.liked_by,
                    "blocks": user.blocks,
                    "blocked_by": user.blocked_by,
                    "reports": user.reports,
                    "reports_by": user.reported_by,
                }
                return result

            except SQLAlchemyError as e:
                print(f"Error getting relationships: {e}")
                return {}

    def is_block(self, user_id, target_id):
        try:
            list_of_blocked = self.get_user_relationships(user_id)["blocks"]
            list_of_blocked_id = [user.user_id for user in list_of_blocked]
            if target_id in list_of_blocked_id:
                return True
            else:
                return False
        except Exception as e:
            print(f"in is block Error: {e}")
            return False

    def is_report(self, user_id, target_id):
        try:
            list_of_reported = self.get_user_relationships(user_id)["reports"]
            list_of_reported_id = [user.user_id for user in list_of_reported]
            if target_id in list_of_reported_id:
                return True
            else:
                return False
        except Exception as e:
            print(f"in is report Error: {e}")
            return False

    def is_friend(self, user_id, target_id):
        try:
            list_of_fiends = self.get_user_relationships(user_id)["friends"]
            list_of_friends_id = [user.user_id for user in list_of_fiends]
            if target_id in list_of_friends_id:
                return True
            else:
                return False
        except Exception as e:
            print(f"in is report Error: {e}")
            return False

    def is_liked(self, user_id, target_id):
        try:
            list_of_likes = self.get_user_relationships(user_id)["likes"]
            list_of_likes_id = [user.user_id for user in list_of_likes]
            if target_id in list_of_likes_id:
                return True
            else:
                return False
        except Exception as e:
            print(f"in is report Error: {e}")
            return False


# ___________________________________________________________________________________________
# ____________________________Class of Gold & Dollar data base ______________________________
# ___________________________________________________________________________________________


class GoldPriceDatabase:
    """
    Manages database operations for gold and dollar prices.
    Interacts with the 'gold' table.
    """

    def __init__(self):
        """
        Initializes the database engine and session maker, and creates tables if they don't exist.
        """
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)  # Creates all tables defined by Base
        self.Session = sessionmaker(bind=self.engine)  # Creates a session factory
        self.on_check = None  # Flag to prevent multiple concurrent price checks

    # ________________________________adding new price to the db manually________________________

    def add_price(
        self,
        gold_18k_ir: float,
        dollar_ir_rial: float,
        time_check_ir: datetime,
        gold_18k_international_dollar: float,
        gold_18k_international_rial: float,
        time_check_int: datetime,
    ):
        """
        Adds a new entry of gold and dollar prices to the database.

        Args:
            gold_18k_ir (float): Price of 18k gold in Iranian Rial.
            dollar_ir_rial (float): Price of US Dollar in Iranian Rial.
            time_check_ir (datetime): Timestamp of the Iranian price check.
            gold_18k_international_dollar (float): International price of 18k gold in USD.
            gold_18k_international_rial (float): International price of 18k gold converted to Rial.
            time_check_int (datetime): Timestamp of the international price check.
        """
        session = self.Session()
        check = GoldDollarRial(
            gold_18k_ir=gold_18k_ir,
            dollar_ir_rial=dollar_ir_rial,
            time_check_ir=time_check_ir,
            gold_18k_international_dollar=gold_18k_international_dollar,
            gold_18k_international_rial=gold_18k_international_rial,
            time_check_int=time_check_int,
        )
        session.add(check)
        session.commit()
        session.close()

    # ________________________________Getting latest update from db_______________________________
    def get_latest_price(self) -> Optional[GoldDollarRial]:
        """
        Retrieves the latest gold and dollar price entry from the database.

        Returns:
            Optional[GoldDollarRial]: The latest GoldDollarRial object if found, None otherwise.
        """
        session = self.Session()
        try:
            return (
                session.query(GoldDollarRial)
                .order_by(GoldDollarRial.check_id.desc())
                .first()
            )
        finally:
            session.close()

    # ___________________Checking latest ir update from db (validate_time)__________________________
    def latest_ir_update(self, validate_time: int = 600) -> Optional[bool]:
        """
        Checks if the latest Iranian price update in the database is older than 'validate_time' seconds.

        Args:
            validate_time (int): The maximum age in seconds for a price to be considered fresh. Defaults to 600 (10 minutes).

        Returns:
            bool: True if an update is needed (data is older than validate_time or no data exists), False otherwise.
        """
        latest_check = self.get_latest_price()
        if latest_check:
            latest_ir_check = latest_check.time_check_ir
            difference = datetime.now() - latest_ir_check
            if difference.seconds > validate_time:
                return True
        else:  # No entry exists, so an update is needed
            return True

    # ___________________Checking latest int update from db (validate_time)__________________________
    def latest_int_update(self, validate_time: int = 600) -> bool:
        """
        Checks if the latest international price update in the database is older than 'validate_time' seconds.

        Args:
            validate_time (int): The maximum age in seconds for a price to be considered fresh. Defaults to 600 (10 minutes).

        Returns:
            bool: True if an update is needed (data is older than validate_time or no data exists), False otherwise.
        """
        latest_check = self.get_latest_price()
        if latest_check:
            latest_int_check = latest_check.time_check_int
            difference = datetime.now() - latest_int_check

            if difference.seconds > validate_time:
                return True
        else:  # No entry exists, so an update is needed
            return True

    # ________combine of all top function to check time valide and chose from where to update_________
    async def get_latest_update(self) -> Optional[GoldDollarRial]:
        """
        Retrieves the latest gold and dollar prices, updating them from external sources if necessary.
        Uses a lock to prevent concurrent updates.

        Returns:
            Optional[GoldDollarRial]: The latest GoldDollarRial object (either fetched or from DB).
        """
        latest_check = self.get_latest_price()

        # If another check is in progress, wait and return the cached data
        if self.on_check:
            logging.info(
                "Another update is in progress. Returning the latest cached price."
            )
            return latest_check  # Return cached/latest instead of risky recursion

        self.on_check = True  # Acquire the lock
        print(self.latest_ir_update(), self.latest_int_update())
        try:
            async with httpx.AsyncClient() as client:
                # Check if Iranian site needs update
                if not self.latest_ir_update():
                    # If IR is up-to-date, check if International site also needs update
                    if not self.latest_int_update():
                        logging.info(
                            "Both IR and INT data are up-to-date in DB. No need to fetch."
                        )

                        pass  # Both are fine, use DB value
                    else:
                        # Only INT site needs update, IR is valid from DB
                        try:
                            logging.info("Fetching INT site data only.")
                            gold_18k_ir = latest_check.gold_18k_ir
                            dollar_ir = latest_check.dollar_ir_rial
                            time_check_ir = latest_check.time_check_ir

                            # Fetch international prices, passing the current dollar rate
                            (
                                gold_18k_int_dlr,
                                gold_18k_int_rial,
                                check_time_int,
                            ) = await site_checker_gold.get_int_gold_to_dollar_to_rial(
                                client, price_dollar_rial=dollar_ir
                            )

                            # Add the updated price entry to the database
                            self.add_price(
                                float(
                                    gold_18k_ir
                                ),  # Assuming gold_18k_ir is already float or can be cleaned
                                float(
                                    dollar_ir
                                ),  # Assuming dollar_ir is already float or can be cleaned
                                time_check_ir,
                                float(gold_18k_int_dlr),
                                float(gold_18k_int_rial),
                                check_time_int,
                            )
                        except Exception as e:
                            logging.error(f"Error fetching INT site data: {e}")
                else:
                    # Both IR and INT sites need updating
                    try:
                        logging.info("Fetching both IR and INT site data.")
                        (
                            gold_18k_ir,
                            dollar_ir,
                            time_check_ir,
                        ) = await site_checker_gold.get_ir_gold_dollar(
                            client
                        )  # Fetch Iranian prices
                        (
                            gold_18k_int_dlr,
                            gold_18k_int_rial,
                            check_time_int,
                        ) = await site_checker_gold.get_int_gold_to_dollar_to_rial(
                            client,
                            price_dollar_rial=dollar_ir,  # Fetch international prices using the newly fetched dollar rate
                        )

                        # Add the combined updated price entry to the database
                        self.add_price(
                            float(
                                gold_18k_ir.replace(",", "")
                            ),  # Clean and convert to float
                            float(
                                dollar_ir.replace(",", "")
                            ),  # Clean and convert to float
                            time_check_ir,
                            float(gold_18k_int_dlr),
                            float(gold_18k_int_rial),
                            check_time_int,
                        )
                    except Exception as e:
                        print(f"error: {e}")
                        logging.error(f"Error fetching both IR and INT site data: {e}")

        finally:
            self.on_check = False  # Always release the lock, even if an error occurs

        return self.get_latest_price()  # Return the latest price after potential update


# ___________________________________________________________________________________________
# ________________________________Class of Users data base __________________________________
# ___________________________________________________________________________________________


class UserDatabase:
    """
    Manages database operations for user-related data.
    Interacts with the 'users' table.
    """

    def __init__(self):
        """
        Initializes the database engine and session maker, and creates tables if they don't exist.
        """
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)  # Creates all tables defined by Base
        self.Session = sessionmaker(bind=self.engine)  # Creates a session factory

    def get_user_data(self, user_id: int, user_data: dict):
        """
        Retrieves user data for a given user ID. If the user does not exist,
        a new User record is created with default registration date.
        The retrieved/created user's attributes are populated into the 'user_data' dictionary.

        Args:
            user_id (int): The ID of the user.
            user_data (dict): A dictionary to populate with the user's data.
        """
        session = self.Session()
        # Query for an existing user
        user = session.query(User).filter_by(user_id=str(user_id)).first()

        # If user does not exist, create a new one
        if not user:
            user = User(user_id=str(user_id))
            user.registration_date = (
                datetime.now()
            )  # Set registration date for new user

        # Use inspect to iterate over columns and populate user_data dictionary
        inspector = inspect(user)
        for column in inspector.mapper.column_attrs:
            column_name = column.key
            column_value = getattr(user, column_name)
            user_data[column_name] = column_value

        session.add(user)  # Add (or re-add if existing) the user object to the session
        session.commit()  # Commit changes (persists new user or updates existing one if modified)
        session.close()

    def generate_user_special_id(self, max_attempts: int = 25) -> str:
        """
        Generates a unique special ID for new users. It retries generation
        up to `max_attempts` times to ensure uniqueness.

        Args:
            max_attempts (int): Maximum number of generation attempts before failing.

        Returns:
            str: A unique generated ID.

        Raises:
            RuntimeError: If unable to generate a unique ID after max_attempts.
        """
        attempt = 0
        while attempt < max_attempts:
            generated_id = generate_secure_random_id()  # Generate a new random ID

            try:
                with self.Session() as session:
                    # Check if the generated ID already exists in the database
                    exists = session.query(
                        session.query(User)
                        .filter_by(generated_id=generated_id)
                        .exists()
                    ).scalar()  # .scalar() returns True/False

                    if not exists:
                        return generated_id  # Found a unique ID, return it

                    attempt += 1  # ID exists, try again
            except Exception as e:
                print(f"Error generating user ID (attempt {attempt + 1}): {e}")
                attempt += 1  # Log error and try again
                continue

        # If loop finishes, it means a unique ID could not be generated
        raise RuntimeError(
            f"Failed to generate unique ID after {max_attempts} attempts"
        )

    def get_user_information(self, target_id: int) -> Optional[User]:
        """
        Searches for a user with the provided user ID and returns their data.

        Args:
            target_id (int): The user ID of the target user.

        Returns:
            Optional[User]: The User object if found, None otherwise.
        """
        with self.Session() as session:
            try:
                user = session.query(User).filter_by(user_id=str(target_id)).first()
                return user
            except Exception as e:
                logging.error(f"Database error fetching user {target_id}: {e}")
                return None

    def update_len(self, user_id: int, language: str):
        with self.Session() as session:
            try:
                user = session.query(User).filter_by(user_id=user_id).first()
                user.language = language
                session.commit()
            except Exception as e:
                logging.error(f"Database error updating language {user_id}: {e}")

    def add_or_update_user(self, user_id: int, user_data: dict):
        """
        Adds a new user or updates an existing user's information in the database.
        If a user with the given user_id does not exist, a new user is created
        with a generated_id and registration_date.

        Args:
            user_id (int): The ID of the user to add or update.
            user_data (dict): A dictionary containing the user's data to be updated.
                              Can include 'generated_id', 'name', 'gender', etc.
        Raises:
            Exception: If a database error occurs during the operation.
        """
        session = self.Session()
        try:
            # Try to find an existing user
            user = session.query(User).filter_by(user_id=str(user_id)).first()

            if not user:
                # If user doesn't exist, create a new one
                generated_id = self.generate_user_special_id()
                user = User(user_id=str(user_id), generated_id=generated_id)
                user.registration_date = datetime.now()
                user_data["generated_id"] = generated_id
                user_data["name"] = user_data["generated_id"]
                user_data["lan"] = "en"
            # If user exists but somehow doesn't have a generated_id, create one
            elif not user.generated_id:
                generated_id = self.generate_user_special_id()
                user.generated_id = generated_id  # Update the user object directly
                user_data["generated_id"] = (
                    generated_id  # Also update user_data to reflect this
                )

            # Ensure user_data is not None if it was passed empty
            if not user_data:
                user_data = {}

            user_data["lan"] = user.language
            # Handle case for existing users who might not have a 'generated_id' in user_data
            # This ensures that even if user_data doesn't explicitly provide it, the existing one is used
            # or a new one is generated if missing from the DB.
            if "generated_id" not in user_data or not user_data["generated_id"]:
                # If generated_id is missing from user_data, try to get it from the user object or generate
                user_data["generated_id"] = (
                    user.generated_id
                    if user.generated_id
                    else self.generate_user_special_id()
                )
                if (
                    not user.generated_id
                ):  # If still missing after fetching, assign the newly generated one
                    user.generated_id = user_data["generated_id"]

            # Update all fields provided in user_data
            for key, value in user_data.items():
                if hasattr(
                    user, key
                ):  # Check if the attribute exists on the User model
                    setattr(user, key, value)

            user.last_online = datetime.now()  # Update last online timestamp
            session.add(user)  # Add the user object to the session (for new or updated)
            session.commit()  # Commit changes to the database
        except Exception as e:
            session.rollback()  # Rollback in case of any error
            raise e
        finally:
            session.close()

    def get_all_users(self) -> Optional[list[Type[User]]]:
        """
        Retrieves all users from the database, ordered by their last online time in descending order.

        Returns:
            List[User]: A list of all User objects. Returns an empty list if no users are found.
        """
        session = self.Session()
        try:
            return session.query(User).order_by(User.last_online.desc()).all()
        finally:
            session.close()

    def get_users_online_time(self, time_min: int) -> List[User]:
        """
        Retrieves users who have been online within a specified time frame.

        Args:
            time_min (int): The number of minutes within which a user is considered online.

        Returns:
            List[User]: A list of User objects who were online within the specified minutes.
        """
        with self.Session() as session:
            time_threshold = datetime.now() - timedelta(minutes=time_min)
            # Select users where last_online is greater than or equal to the time threshold
            query = (
                select(User)
                .where(User.last_online >= time_threshold)
                .order_by(User.last_online.desc())
            )
            return session.execute(query).scalars().all()

    def get_users_apply_system_sorting_by_db(
        self, user_id: int, max_km: float = 9999999.0
    ) -> List[dict]:
        """
        Retrieves users located near the requesting user, filtering by maximum distance.
        Includes calculated distance, minutes since last online, and online status.

        Args:
            user_id (int): The ID of the requesting user.
            max_km (float): The maximum distance in kilometers to include other users.

        Returns:
            List[dict]: A list of dictionaries, each containing a 'user' object,
                        'distance', 'mins_ago', and 'is_online' status.
                        Returns an empty list if the requesting user's location is unavailable
                        or no nearby users are found.
        """
        with self.Session() as session:
            # 1. Get the requesting user's location
            requesting_user = session.get(User, user_id)
            if not requesting_user:
                return []  # Return empty if requesting user

            if not requesting_user.latitude:
                all_users = (
                    session.query(User)
                    .filter(
                        User.latitude.isnot(None),
                        User.longitude.isnot(None),
                        User.user_id
                        != requesting_user.user_id,  # Exclude the requesting user itself
                    )
                    .all()
                )
                now = datetime.now()
                nearby_users = []
                print(all_users)
                for user in all_users:
                    mins_ago = (now - user.last_online).total_seconds() / 60
                    is_online = (
                            mins_ago <= 1
                    )
                    nearby_users.append(
                            {
                                "user": user,
                                "distance":"xXx",
                                "mins_ago": mins_ago,
                                "is_online": is_online,
                            }
                        )
                return sorted(
                    nearby_users,
                    key=lambda x: (
                        not x["is_online"],  # Online users first (False sorts before True)
                        x["mins_ago"],  # Then by minutes since last online
                    ),
                )
            else:

                # 2. Get all users (or better: filter nearby users directly in SQL)
                # Exclude self and ensure other users have location data

                all_users = (
                    session.query(User)
                    .filter(
                        User.latitude.isnot(None),
                        User.longitude.isnot(None),
                        User.user_id
                        != requesting_user.user_id,  # Exclude the requesting user itself
                    )
                    .all()
                )

                # 3. Calculate distances and online status for each user
                now = datetime.now()
                nearby_users = []

                for user in all_users:
                    distance = self._calculate_distance(
                        requesting_user.latitude,
                        requesting_user.longitude,
                        user.latitude,
                        user.longitude,
                    )

                    if distance <= max_km:
                        # Calculate minutes since last online
                        mins_ago = (now - user.last_online).total_seconds() / 60
                        is_online = (
                            mins_ago <= 1
                        )  # Consider online if active in last 1 minute

                        nearby_users.append(
                            {
                                "user": user,
                                "distance": distance,
                                "mins_ago": mins_ago,
                                "is_online": is_online,
                            }
                        )

                # 4. Sort by: online status first, then by minutes ago, then by distance
                return sorted(
                    nearby_users,
                    key=lambda x: (
                        not x["is_online"],  # Online users first (False sorts before True)
                        x["mins_ago"],  # Then by minutes since last online
                        x["distance"],  # Then by distance
                    ),
                )

    @staticmethod
    def _calculate_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculates the distance between two geographical points using the Haversine formula.

        Args:
            lat1 (float): Latitude of the first point.
            lon1 (float): Longitude of the first point.
            lat2 (float): Latitude of the second point.
            lon2 (float): Longitude of the second point.

        Returns:
            float: The distance between the two points in kilometers.
        """
        R = 6371  # Radius of Earth in kilometers

        # Convert degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def get_user_generated_id(self, user_id: int) -> Optional[str]:
        """
        Retrieves the system-generated ID for a user based on their user ID.

        Args:
            user_id (int): The integer user ID to look up.

        Returns:
            Optional[str]: The generated ID string if found, None otherwise.
        """
        try:
            with self.Session() as session:
                # Using scalar() for single-value queries is more efficient
                generated_id = session.execute(
                    select(User.generated_id).where(User.user_id == user_id)
                ).scalar()
                if generated_id:
                    return generated_id if generated_id else None
                return None  # Explicitly return None if no generated_id found

        except SQLAlchemyError as e:
            # logger.error(f"Database error fetching generated ID for user {user_id}: {e}",
            print(f"Error fetching generated ID for user {user_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_user_generated_id: {e}")
            return None

    def get_user_id_from_generated_id(self, generated_id: str) -> Optional[int]:
        """
        Retrieves the user ID for a user based on their system-generated ID.

        Args:
            generated_id (str): The system-generated ID to look up.

        Returns:
            Optional[int]: The User ID (integer) if found, None otherwise.
        """
        try:
            with self.Session() as session:
                # Using scalar() for single-value queries is more efficient
                user_id = session.execute(
                    select(User.user_id).where(User.generated_id == generated_id)
                ).scalar()
                if user_id:
                    return user_id if user_id else None
                return None  # Explicitly return None if no user_id found

        except SQLAlchemyError as e:
            # logger.error(f"Database error fetching generated ID for user {user_id}: {e}",
            print(f"Error fetching generated Generated ID for user {generated_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in user_id from generated_id: {e}")
            return None


# ___________________________________________________________________________________________
# _________________simple way of input a list of towns (this can be in db ___________________
# ___________________________________________________________________________________________

# A list of Iranian cities in Persian, used for filtering or selection.
iran_cities_fa = [
    "تهران",
    "مشهد",
    "اصفهان",
    "کرج",
    "شیراز",
    "تبریز",
    "قم",
    "اهواز",
    "کرمانشاه",
    "ارومیه",
    "رشت",
    "زاهدان",
    "همدان",
    "کرمان",
    "یزد",
    "اردبیل",
    "بندرعباس",
    "گرگان",
    "ساری",
    "قم",
    "خرم آباد",
    "سنندج",
    "دزفول",
    "بوشهر",
    "بیرجند",
    "سبزوار",
    "نجف اباد",
    "بروجرد",
    "ملایر",
    "قزوین",
]


# ___________________________________________________________________________________________
# ________________________________Class of Users Chat base __________________________________
# ___________________________________________________________________________________________


class ChatDatabase:
    """
    Manages database operations for user chat sessions, messages, and links.
    Interacts with 'users_sessions', 'message_map', and 'links' tables.
    """

    def __init__(self):
        """
        Initializes the database engine and session maker, and creates tables if they don't exist.
        """
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)  # Creates all tables defined by Base
        self.Session = sessionmaker(bind=self.engine)  # Creates a session factory

    def reset_db(self):
        """
        Resets the database by adding a new column to 'message_map' table.
        This function is intended for early development only and should be used with caution.
        """
        with self.engine.connect() as conn:
            # This line attempts to add a new column 'msg_txt' to 'message_map' table.
            # It will raise an error if the column already exists.
            conn.execute(text("ALTER TABLE message_map ADD COLUMN msg_txt TEXT"))
            conn.commit()

    def create_user_session(self, user_id: int):
        """
        Ensures a user has an entry in the 'users_sessions' database table.
        If a session for the user_id does not exist, a new one is created.

        Args:
            user_id (int): The ID of the user.
        """
        with self.Session() as session:
            # Check if a session for the user already exists
            if not session.query(Sessions).filter_by(user_id=user_id).first():
                new_session = Sessions(
                    user_id=user_id
                )  # Create a new session if not found
                session.add(new_session)
                session.commit()

    def add_partner(self, user_id: int, partner_id: int) -> bool:
        """
        Adds a partner for a user. This establishes a one-sided partnership.

        Args:
            user_id (int): ID of the user who is adding a partner.
            partner_id (int): ID of the user to be added as a partner.

        Returns:
            bool: True if the partner was successfully added, False otherwise.
                  Returns False if either user does not exist or a database error occurs.
        """
        with self.Session() as session:
            try:
                # Verify both user sessions exist
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()
                user2 = session.query(Sessions).filter_by(user_id=partner_id).first()

                if not user1 or not user2:
                    return False  # One or both users do not have a session

                # Check if already partners (one-sided check)
                if user1.partner_id == partner_id:
                    return True  # Already partners, no change needed

                # Establish partnership for user1
                user1.partner_id = partner_id
                session.commit()
                return True

            except Exception as e:
                session.rollback()  # Rollback on error
                print(f"Error adding partner {partner_id}: {e}")
                return False

    def remove_partner(self, user_id: int) -> bool:
        """
        Removes the current partner of a user. This is a one-sided removal.

        Args:
            user_id (int): ID of the user whose partner is to be removed.

        Returns:
            bool: True if the partner was successfully removed, False otherwise.
                  Returns False if the user does not exist or a database error occurs.
        """
        with self.Session() as session:
            try:
                # Verify the user's session exists
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()

                if not user1:
                    return False  # User session not found

                # Set partner_id to None to remove the partnership
                user1.partner_id = None
                session.commit()
                return True

            except Exception as e:
                session.rollback()  # Rollback on error
                print(f"Error removing partner of {user_id} : {e}")
                return False

    def set_partnership(self, user_id: int, partner_id: int) -> bool:
        """
        Establishes a mutual partnership between two users. Both users will have
        each other set as their partner_id.

        Args:
            user_id (int): ID of the first user.
            partner_id (int): ID of the second user.

        Returns:
            bool: True if partnership was successfully established, False otherwise.
                  Returns False if either user doesn't exist, they are already partners,
                  or a database error occurs.
        """
        with self.Session() as session:
            try:
                # Verify both user sessions exist
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()
                user2 = session.query(Sessions).filter_by(user_id=partner_id).first()

                if not user1 or not user2:
                    return False  # One or both users do not have a session

                # Check if they are already mutual partners
                if user1.partner_id == partner_id and user2.partner_id == user_id:
                    return True  # Already partners, no change needed

                # Establish mutual partnership
                user1.partner_id = partner_id
                user2.partner_id = user_id
                session.commit()
                return True

            except Exception as e:
                session.rollback()  # Rollback on error
                print(
                    f"Error establishing partnership between {user_id} and {partner_id}: {e}"
                )
                return False

    def remove_partnership(self, user_id: int) -> bool:
        """
        Removes a mutual partnership from a user and their current partner.
        The `partner_id` and `perv_partner_id` are updated for both users.

        Args:
            user_id (int): ID of the user initiating the partnership removal.

        Returns:
            bool: True if partnership was successfully broken, False otherwise.
                  Returns False if the user or their partner's session doesn't exist
                  or a database error occurs.
        """
        with self.Session() as session:
            try:
                # Verify the user's session exists
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()
                if not user1:
                    return False  # User session not found

                partner_id = user1.partner_id
                if not partner_id:
                    return True  # No partner to remove for user1
                user2 = session.query(Sessions).filter_by(user_id=partner_id).first()

                if not user2:  # Partner's session not found, but user1 might still have a partner_id
                    user1.perv_partner_id = user1.partner_id
                    user1.partner_id = None
                    session.commit()
                    return True

                # Update user1's partnership status
                if user1.partner_id == partner_id:
                    user1.perv_partner_id = (
                        user1.partner_id
                    )  # Store current partner as previous
                    user1.partner_id = None  # Remove current partner

                # Update user2's (the partner's) partnership status
                if user2.partner_id == user_id:
                    user2.perv_partner_id = (
                        user2.partner_id
                    )  # Store current partner as previous
                    user2.partner_id = None  # Remove current partner

                session.commit()
                return True

            except Exception as e:
                session.rollback()  # Rollback on error
                print(
                    f"Error establishing partnership between {user_id} and other person: {e}"
                )
                return False

    def get_user_session(self, user_id: int) -> Optional[Sessions]:
        """
        Retrieves a user's session object by their ID.

        Args:
            user_id (int): The ID of the user whose session to retrieve.

        Returns:
            Optional[Sessions]: The Sessions object if found, None otherwise.
        """
        with self.Session() as session:
            try:
                return session.query(Sessions).filter_by(user_id=user_id).first()
            except Exception as e:
                print(f"Error fetching session for user {user_id}: {e}")
                return None

    def get_partner_id(self, user_id: int) -> Optional[int]:
        """
        Retrieves the partner ID of a given user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Optional[int]: The partner's user ID if a partner exists, None otherwise.
        """
        try:
            session_obj = self.get_user_session(user_id)
            if session_obj:
                return session_obj.partner_id
            else:
                print(
                    f"No session found for user {user_id} when trying to get partner ID."
                )
                return None
        except Exception as e:
            print(f"Could not get partner id: {e}")
            return None

    def cleanup_expired_links(self):
        """
        Deactivates links in the database that have passed their expiration time.
        """
        with self.Session() as session:
            try:
                session.query(Links).filter(
                    Links.expire_time
                    < datetime.now()  # Filter links older than current time
                ).update({"active": False})  # Set 'active' to False for expired links
                session.commit()
            except Exception as e:
                session.rollback()  # Rollback on error
                print(f"Error cleaning links: {e}")

    def add_link(
        self,
        link: str,
        user_id: int,
        exp_time_hr: int = 24,
        max_uses: Optional[int] = None,
    ) -> Optional[Links]:
        """
        Adds a new link/token to the database with an owner, expiration, and optional max uses.

        Args:
            link (str): The unique token/link identifier.
            user_id (int): The ID of the user who owns the link.
            exp_time_hr (int): The expiration time in hours from now. Defaults to 24.
            max_uses (Optional[int]): The maximum allowed uses for the link. None means unlimited uses.

        Returns:
            Optional[Links]: The created Links object if successful, None if failed.

        Raises:
            ValueError: If the `user_id` does not have an existing session.
        """
        self.cleanup_expired_links()  # Clean up expired links before adding a new one
        with self.Session() as session:
            # Verify that the user_id exists in users_sessions
            if not session.query(Sessions).filter_by(user_id=user_id).first():
                raise ValueError(f"User {user_id} has no session!")
            try:
                new_link = Links(
                    link=link,
                    owner_id=str(
                        user_id
                    ),  # Store user_id as string if needed, or int if column is int
                    expire_time=datetime.now()
                    + timedelta(hours=exp_time_hr),  # Calculate expiration time
                    max_uses=max_uses,
                )

                session.add(new_link)
                session.commit()
                return new_link
            except Exception as e:
                session.rollback()  # Rollback on error
                print(f"Failed to add link: {e}")
                return None

    def get_link(self, link: str) -> Optional[Links]:
        """
        Retrieves a link by its token if it exists, is active, and not expired.
        Automatically cleans up expired links first.

        Args:
            link (str): The link token to retrieve.

        Returns:
            Optional[Links]: The Links object if found and valid, None otherwise.
        """
        self.cleanup_expired_links()  # Ensure expired links are deactivated before lookup

        with self.Session() as session:
            try:
                link_obj = (
                    session.query(Links)
                    .filter(
                        Links.link == link,
                        Links.active == True,  # Only retrieve active links
                        Links.expire_time
                        >= datetime.now(),  # Only retrieve non-expired links
                    )
                    .first()
                )
                return link_obj
            except Exception as e:
                print(f"Error fetching link: {e}")
                return None

    def get_link_owner(self, link: str) -> Optional[int]:
        """
        Retrieves the owner ID of a given link if the link is valid.
        Automatically cleans up expired links first.

        Args:
            link (str): The link token.

        Returns:
            Optional[int]: The owner's user ID if the link is found and valid, None otherwise.
        """
        self.cleanup_expired_links()  # Clean up expired links first

        link_obj = self.get_link(link)  # Reuse the get_link method
        return (
            int(link_obj.owner_id) if link_obj and link_obj.owner_id else None
        )  # Ensure owner_id is returned as int

    def decrement_link_use(self, link: str) -> bool:
        """
        Decrements the remaining uses of a link. If max_uses reaches 0 or
        the link expires, it is marked as inactive.

        Args:
            link (str): The link token to decrement uses for.

        Returns:
            bool: True if decrement was successful, False otherwise (e.g., link not found,
                  expired, or no remaining uses).
        """
        with self.Session() as session:
            link_obj = session.query(Links).filter_by(link=link).first()
            if not link_obj:
                return False  # Link does not exist

            # Check if link is expired
            if link_obj.expire_time <= datetime.now():
                link_obj.active = False  # Mark as inactive
                session.commit()
                return False

            # Check and decrement max_uses if applicable
            if link_obj.max_uses is not None:
                if link_obj.max_uses <= 0:
                    link_obj.active = False  # Mark as inactive if no uses left
                    session.commit()
                    return False
                link_obj.max_uses -= 1  # Decrement remaining uses

            link_obj.number_of_used += 1  # Increment the total number of times used
            session.commit()
            return True

    def get_msg_id_by_robot_msg(self, robot_msg_id: int) -> Optional[int]:
        """
        Gets the internal `message_id` from `MessageMap` corresponding to a bot's message ID.

        Args:
            robot_msg_id (int): The bot's message ID (e.g., from Telegram API).

        Returns:
            Optional[int]: The internal `message_id` if found, None otherwise.
        """
        with self.Session() as session:
            try:
                msg_obj = (
                    session.query(MessageMap)
                    .filter_by(bot_message_id=robot_msg_id)
                    .first()
                )
                return msg_obj.message_id if msg_obj else None
            except Exception as e:
                print(f"Error fetching message for bot message: {robot_msg_id}: {e}")
                return None

    def get_msg_id_by_user_msg(self, user_msg_id: int) -> Optional[int]:
        """
        Gets the bot's `bot_message_id` from `MessageMap` corresponding to an internal user message ID.

        Args:
            user_msg_id (int): The internal user message ID.

        Returns:
            Optional[int]: The bot's `bot_message_id` if found, None otherwise.
        """
        with self.Session() as session:
            try:
                msg_obj = (
                    session.query(MessageMap).filter_by(message_id=user_msg_id).first()
                )
                return msg_obj.bot_message_id if msg_obj else None
            except Exception as e:
                print(f"Error fetching message for user message: {user_msg_id}: {e}")
                return None

    def map_message(
        self,
        user_msg: int,
        bot_msg: int,
        user_id: int,
        partner_id: int,
        msg_txt: Optional[str] = None,
    ) -> bool:
        """
        Maps an incoming user message to an outgoing bot message for chat tracking.

        Args:
            user_msg (int): The ID of the message sent by the user.
            bot_msg (int): The ID of the message sent by the bot to the partner.
            user_id (int): The ID of the user who sent the message.
            partner_id (int): The ID of the user who received the message (via bot).
            msg_txt (Optional[str]): The text content of the message. Defaults to None.

        Returns:
            bool: True if the message was successfully mapped, False otherwise.
        """
        new_msg = MessageMap(
            message_id=user_msg,
            bot_message_id=bot_msg,
            sender_id=user_id,
            receiver_id=partner_id,
            time=datetime.now(),
            msg_txt=msg_txt,
        )
        try:
            with self.Session() as session:
                session.add(new_msg)
                session.commit()
                return True
        except Exception as e:
            print(f"Could not map message with message id: {user_msg} : {e}")
            return False

    def secret_chat_toggle(
        self, user_id: int, hand_change: Optional[bool] = None
    ) -> bool:
        """
        Toggles or sets the secret chat status for a user.

        Args:
            user_id (int): ID of the user to modify.
            hand_change (Optional[bool]): If None, toggles the current state.
                                           If True, sets secret chat to True.
                                           If False, sets secret chat to False.

        Returns:
            bool: True if the status was successfully updated, False if an error occurred
                  or the user session was not found.
        """
        with self.Session() as session:
            try:
                session_obj = session.query(Sessions).filter_by(user_id=user_id).first()
                if not session_obj:
                    print(f"No session found for user {user_id}")
                    return False

                # Toggle or set based on hand_change argument
                session_obj.secret_chat = (
                    not session_obj.secret_chat if hand_change is None else hand_change
                )

                session.commit()
                return True

            except Exception as e:
                session.rollback()  # Rollback on error
                print(f"Error toggling secret chat for user {user_id}: {e}")
                return False

    def get_user_messages(self, user_id: int) -> Optional[List[MessageMap]]:
        """
        Retrieves all messages sent by a specific user from the message map.
        Messages are ordered by time in descending order (most recent first).

        Args:
            user_id (int): The ID of the user whose messages to retrieve.

        Returns:
            Optional[List[MessageMap]]: A list of MessageMap objects if messages are found,
                                       None otherwise.
        """
        with self.Session() as session:
            try:
                messages = (
                    session.query(MessageMap)
                    .filter(MessageMap.sender_id == user_id)
                    .order_by(MessageMap.time.desc())
                    .all()
                )
                return messages if messages else None
            except Exception as e:
                print(f"Error fetching messages for user {user_id}: {str(e)}")
                return None

    def get_previous_partner_messages(
        self, user_id: int, perv_partner_id: int
    ) -> Optional[List[MessageMap]]:
        """
        Retrieves chat messages between a user and a previous partner.
        Messages are ordered by time in descending order.

        Args:
            user_id (int): The ID of the current user.
            perv_partner_id (int): The ID of the previous partner.

        Returns:
            Optional[List[MessageMap]]: A list of MessageMap objects representing the conversation,
                                       or None if no messages are found or an error occurs.
        """
        with self.Session() as session:
            try:
                messages = (
                    session.query(MessageMap)
                    .filter(
                        (MessageMap.sender_id == user_id)
                        | (
                            MessageMap.receiver_id == user_id
                        ),  # Messages sent by user_id or received by user_id
                        (MessageMap.sender_id == perv_partner_id)
                        | (
                            MessageMap.receiver_id == perv_partner_id
                        ),  # Messages involving perv_partner_id
                    )
                    .order_by(MessageMap.time.desc())
                    .all()
                )
                return messages if messages else None
            except Exception as e:
                print(
                    f"Error fetching previous partner messages for user {user_id} with partner {perv_partner_id}: {str(e)}"
                )
                return None

    def clear_msg_map(
        self, exp_time: Optional[int] = None, user_id: Optional[int] = None
    ) -> tuple[int, Optional[str]]:
        """
        Clears entries from the `message_map` table based on expiration time and/or user ID.

        Args:
            exp_time (Optional[int]): Hours before now to delete older messages.
            user_id (Optional[int]): Delete messages where this user is either sender or receiver.

        Returns:
            tuple: A tuple containing:
                   - int: The number of deleted messages.
                   - Optional[str]: An error message if any, None otherwise.
        """
        if not exp_time and not user_id:
            return (0, "Please provide either exp_time or user_id")

        deleted_count = 0
        with self.Session() as session:
            try:
                query = session.query(MessageMap)

                # Build filters
                filters = [
                    MessageMap.requested == False
                ]  # Only delete non-requested messages

                if exp_time:
                    time_threshold = datetime.now() - timedelta(hours=exp_time)
                    filters.append(MessageMap.time <= time_threshold)
                if user_id:
                    filters.append(
                        (MessageMap.sender_id == user_id)
                        | (MessageMap.receiver_id == user_id)
                    )

                # Execute deletion in a single operation
                if filters:
                    deleted_count = query.filter(*filters).delete(
                        synchronize_session="fetch"
                    )  # Use 'fetch' to ensure accurate count
                    session.commit()

                return (deleted_count, None)

            except Exception as e:
                session.rollback()  # Rollback on error
                error_msg = f"Error clearing message_map: {str(e)}"
                print(error_msg)
                return (0, error_msg)

    def set_random_chat(self, user_id: int, stat: bool) -> bool:
        """
        Sets a user's status for looking for a random chat.

        Args:
            user_id (int): The ID of the user.
            stat (bool): True if the user is looking for a random chat, False otherwise.

        Returns:
            bool: True if the status was successfully updated, False otherwise.
        """
        with self.Session() as session:
            try:
                user_session = (
                    session.query(Sessions).filter_by(user_id=user_id).first()
                )
                if not user_session:
                    print(f"User session not found for {user_id}")
                    return False
                user_session.looking_random_chat = stat
                session.commit()

                # Verify the change (optional, but good for debugging)
                session.refresh(user_session)
                print(
                    f"Updated status for {user_id}: {user_session.looking_random_chat}"
                )
                return True
            except Exception as e:
                print(f"Could not change random chat status: {e}")
                return False

    def get_random_chaters(self, female: bool = True, male: bool = True) -> list:
        """
        Retrieves a list of users who are currently looking for random chats,
        filtered by gender.

        Args:
            female (bool): If True, include female users in the results. Defaults to True.
            male (bool): If True, include male users in the results. Defaults to True.

        Returns:
            list: A list of User objects matching the random chat and gender criteria.
                  Returns an empty list if no users are found or an error occurs.
        """
        with self.Session() as session:
            try:
                # Join Sessions and User tables to get user gender information
                random_users = (
                    session.query(Sessions, User)
                    .join(User, Sessions.user_id == User.user_id)
                    .filter(
                        Sessions.looking_random_chat
                        == True  # Filter for users looking for random chat
                    )
                    .all()
                )

                result = []
                print(random_users)  # For debugging
                for session_obj, user in random_users:
                    if user.gender and user.gender.lower() == "male":
                        if male:  # Include male users if 'male' filter is True
                            result.append(user)
                    elif user.gender and user.gender.lower() == "female":
                        if female:  # Include female users if 'female' filter is True
                            result.append(user)
                    else:
                        # Include users with no specified gender only if neither male nor female is requested
                        if not male and not female:
                            result.append(user)

                return result

            except Exception as e:
                print(f"Error getting random chatters: {e}")
                return []

    def get_msg_requests_from_map(
        self, user_id: int, sender_id: int
    ) -> Optional[List[str]]:
        """
        Retrieves the text of 'requested' messages sent from a specific sender to a user.
        After retrieval, these messages are marked as `requested=False`.

        Args:
            user_id (int): The ID of the receiver user.
            sender_id (int): The ID of the sender user.

        Returns:
            Optional[List[str]]: A list of message texts that were requested, or None if
                                 no messages are found or an error occurs.
        """
        with self.Session() as session:
            try:
                messages = (
                    session.query(MessageMap)
                    .filter_by(
                        receiver_id=user_id,
                        sender_id=sender_id,
                        requested=True,  # Filter for messages marked as requested
                    )
                    .all()
                )

                texts = [
                    msg.msg_txt for msg in messages if msg.msg_txt is not None
                ]  # Extract texts
                for msg in messages:
                    msg.requested = (
                        False  # Mark messages as not requested after retrieval
                    )
                session.commit()

                return texts
            except Exception as e:
                print(f"Could not get request msgs : {e}")
                return None

    def clear_msg_requests_from_map(self, user_id: int, sender_id: int) -> bool:
        """
        Deletes 'requested' messages sent from a specific sender to a user from the message map.

        Args:
            user_id (int): The ID of the receiver user.
            sender_id (int): The ID of the sender user.

        Returns:
            bool: True if the requested messages were successfully deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                messages = (
                    session.query(MessageMap)
                    .filter_by(
                        receiver_id=user_id,
                        sender_id=sender_id,
                        requested=True,  # Filter for messages marked as requested
                    )
                    .all()
                )

                for msg in messages:
                    session.delete(msg)  # Delete each message
                session.commit()

                return True
            except Exception as e:
                print(f"Could not clear request msgs : {e}")
                return False

    def add_requested_msg(self, sender_id: int, receiver_id: int, msg_txt: str) -> bool:
        """
        Adds a new message to the `message_map` table, marking it as 'requested'.
        This is typically used for messages that need explicit user approval or action.

        Args:
            sender_id (int): The ID of the user who sent the message.
            receiver_id (int): The ID of the user who is the intended receiver.
            msg_txt (str): The text content of the requested message.

        Returns:
            bool: True if the message was successfully added, False otherwise.
        """
        with self.Session() as session:
            try:
                new_msg = MessageMap(
                    bot_message_id=6969,  # Placeholder ID, consider making nullable in schema
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    msg_txt=msg_txt,
                    requested=True,  # Mark as a requested message
                    time=datetime.now(),
                )
                session.add(new_msg)
                session.commit()
                return True
            except Exception as e:
                print(f"Error in adding new request msg: {e}")
                return False


class TorobDb:
    """
    Manages database operations for tracking items on Torob (an Iranian price comparison website).
    Interacts with 'torob_item' and 'torob_check' tables.
    """

    def __init__(self):
        """
        Initializes the database engine and session maker, and creates tables if they don't exist.
        """
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)  # Creates all tables defined by Base
        self.Session = sessionmaker(bind=self.engine)  # Creates a session factory

    def add_item(
        self, user_id: int, preferred_price: float, torob_url: str, name: Optional[str]
    ) -> bool:
        """
        Adds a new item to be tracked on Torob to the database.

        Args:
            user_id (int): The ID of the user who wants to track this item.
            preferred_price (float): The user's preferred (target) price for the item.
            torob_url (str): The URL of the item on the Torob website.
            name (Optional[str]): The name of the item.

        Returns:
            bool: True if the item was successfully added, False otherwise.
        """
        with self.Session() as session:
            try:
                new_torob = TorobScrapUser(
                    user_id=user_id,
                    name_of_item=name,
                    user_preferred_price=preferred_price,
                    # tag=name, # Assuming 'tag' is a column not defined, or intended to be 'name_of_item'
                    torob_url=torob_url,
                )
                session.add(new_torob)
                session.commit()
                return True
            except Exception as e:
                print(f"Failed to add item: {e}")
                return False

    def add_check(self, item_id: int, checked_price: float) -> bool:
        """
        Adds a new price check record for a specific item to the database.

        Args:
            item_id (int): The ID of the item for which the price was checked.
            checked_price (float): The price of the item at the time of the check.

        Returns:
            bool: True if the check was successfully added to the database, False otherwise.
        """
        try:
            with self.Session() as session:
                new_check = TorobCheck(item_id=item_id, checked_price=checked_price)
                session.add(new_check)
                session.commit()
                return True
        except Exception as e:
            print(f"Could not add the check: {e}")
            return False

    def get_user_items(self, user_id: int) -> List[Type[TorobScrapUser]]:
        """
        Retrieves a list of all items tracked by a specific user.

        Args:
            user_id (int): The ID of the user whose items are to be retrieved.

        Returns:
            List[TorobScrapUser]: A list of TorobScrapUser objects. Returns an empty list
                                  if no items are found for the user or on error.
        """
        with self.Session() as session:
            try:
                # Query for TorobScrapUser objects filtered by user_id
                # .all() executes the query and returns a list of results
                items = session.query(TorobScrapUser).filter_by(user_id=user_id).all()
                return items
            except Exception as e:
                print(f"Failed to retrieve items for user {user_id}: {e}")
                return []

    def check_ownership(self, user_id: int, item_id: int) -> bool:
        """
        Checks if a given user is the owner of a specific item.

        Args:
            user_id (int): The ID of the user.
            item_id (int): The ID of the item to check ownership for.

        Returns:
            bool: True if this user is the owner of this item, False otherwise.
        """
        try:
            print(user_id)
            user_items = self.get_user_items(user_id)  # Get all items owned by the user
            print(user_items)
            if user_items:
                user_items_id = [
                    item.item_id for item in user_items
                ]  # Extract item IDs
                if item_id in user_items_id:
                    return True  # Item ID found in user's items
                else:
                    print("He/she is not the owner")
                    return False
            else:
                print("User does not have any item yet")
                return False  # User has no items at all
        except Exception as e:
            print(f"Error checking item owner: {e}")
            return False

    def update_preferred_price(self, item_id: int, new_price: float) -> bool:
        """
        Updates the user's preferred price for a specific item.

        Args:
            item_id (int): The ID of the item to update.
            new_price (float): The new preferred price.

        Returns:
            bool: True if the price was updated successfully, False otherwise (e.g., item not found).
        """
        with self.Session() as session:
            try:
                # Find the item by its primary key
                item_to_update = session.query(TorobScrapUser).get(item_id)

                if item_to_update:
                    item_to_update.user_preferred_price = new_price
                    session.commit()
                    return True
                else:
                    print(f"Item with ID {item_id} not found.")
                    return False
            except Exception as e:
                session.rollback()  # Rollback in case of error
                print(f"Failed to update preferred price for item {item_id}: {e}")
                return False

    def update_url(self, item_id: int, new_url: str) -> bool:
        """
        Updates the URL for a specific item.

        Args:
            item_id (int): The ID of the item to update.
            new_url (str): The new URL for the item.

        Returns:
            bool: True if the URL was updated successfully, False otherwise (e.g., item not found or invalid URL format).
        """
        with self.Session() as session:
            try:
                # Find the item by its primary key
                item_to_update = session.query(TorobScrapUser).get(item_id)

                if item_to_update:
                    # Validate URL format if needed (simple check)
                    if not new_url.startswith(("http://", "https://")):
                        print(f"Invalid URL format for item {item_id}")
                        return False

                    item_to_update.torob_url = new_url
                    session.commit()
                    return True
                else:
                    print(f"Item with ID {item_id} not found.")
                    return False
            except Exception as e:
                session.rollback()  # Rollback in case of error
                print(f"Failed to update URL for item {item_id}: {e}")
                return False

    def update_name(self, item_id: int, new_name: str) -> bool:
        """
        Updates the name for a specific item.

        Args:
            item_id (int): The ID of the item to update.
            new_name (str): The new name for the item.

        Returns:
            bool: True if the name was updated successfully, False otherwise (e.g., item not found or name too long).
        """
        with self.Session() as session:
            try:
                # Find the item by its primary key
                item_to_update = session.query(TorobScrapUser).get(item_id)

                if item_to_update:
                    # Validate name length if needed (e.g., assuming a limit of 150 characters)
                    if len(new_name) > 150:
                        print(f"Name too long for item {item_id}")
                        return False

                    item_to_update.name_of_item = new_name
                    session.commit()
                    return True
                else:
                    print(f"Item with ID {item_id} not found.")
                    return False
            except Exception as e:
                session.rollback()  # Rollback in case of error
                print(f"Failed to update name for item {item_id}: {e}")
                return False

    def get_price_history(self, item_id: int) -> List[Type[TorobCheck]]:
        """
        Retrieves a list of all price checks for a specific item, ordered by timestamp.

        Args:
            item_id (int): The ID of the item whose price history is to be retrieved.

        Returns:
            List[TorobCheck]: A list of TorobCheck objects, ordered chronologically by check_timestamp.
                              Returns an empty list if no checks are found or on error.
        """
        with self.Session() as session:
            try:
                # Query for TorobCheck objects filtered by item_id
                # .order_by(TorobCheck.check_timestamp) ensures the history is chronological
                # .all() executes the query
                price_history = (
                    session.query(TorobCheck)
                    .filter_by(item_id=item_id)
                    .order_by(TorobCheck.check_timestamp)
                    .all()
                )
                return price_history
            except Exception as e:
                print(f"Failed to retrieve price history for item {item_id}: {e}")
                return []

    def get_item_by_id(self, item_id: int) -> Optional[TorobScrapUser]:
        """
        Retrieves a single TorobScrapUser item by its primary key.

        Args:
            item_id (int): The ID of the item to retrieve.

        Returns:
            Optional[TorobScrapUser]: The TorobScrapUser object if found, None otherwise.
        """
        with self.Session() as session:
            try:
                # .get() is optimized for primary key lookups
                item = session.query(TorobScrapUser).get(item_id)
                return item
            except Exception as e:
                print(f"Failed to retrieve item {item_id}: {e}")
                return None

    def delete_item(self, item_id: int) -> bool:
        """
        Deletes a TorobScrapUser item and all its associated price checks.
        This requires `cascade="all, delete-orphan"` on the `price_checks` relationship
        in the `TorobScrapUser` model.

        Args:
            item_id (int): The ID of the item to delete.

        Returns:
            bool: True if the item was successfully deleted, False otherwise (e.g., item not found).
        """
        with self.Session() as session:
            try:
                item_to_delete = session.query(TorobScrapUser).get(item_id)
                if item_to_delete:
                    session.delete(item_to_delete)
                    session.commit()
                    print(f"Item {item_id} and its checks deleted successfully.")
                    return True
                else:
                    print(f"Item with ID {item_id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()  # Rollback on error
                print(f"Failed to delete item {item_id}: {e}")
                return False

    def get_latest_price(self, item_id: int) -> Optional[float]:
        """
        Retrieves the most recent checked price for a given item.

        Args:
            item_id (int): The ID of the item.

        Returns:
            Optional[float]: The latest checked price as a float, or None if no checks exist for the item.
        """
        with self.Session() as session:
            try:
                # Query for the latest check by item_id, order by timestamp descending, and take the first one.
                latest_check = (
                    session.query(TorobCheck)
                    .filter_by(item_id=item_id)
                    .order_by(TorobCheck.check_timestamp.desc())
                    .first()
                )
                return latest_check.checked_price if latest_check else None
            except Exception as e:
                print(f"Failed to get latest price for item {item_id}: {e}")
                return None

    def get_latest_check(self, item_id: int) -> Optional[datetime]:
        """
        Retrieves the timestamp of the most recent price check for a given item.

        Args:
            item_id (int): The ID of the item.

        Returns:
            Optional[datetime]: The timestamp of the latest check as a datetime object,
                                or None if no checks exist for the item.
        """
        with self.Session() as session:
            try:
                # Query for the latest check by item_id, order by timestamp descending, and take the first one.
                latest_check = (
                    session.query(TorobCheck)
                    .filter_by(item_id=item_id)
                    .order_by(TorobCheck.check_timestamp.desc())
                    .first()
                )
                return latest_check.check_timestamp if latest_check else None
            except Exception as e:
                print(f"Failed to get latest check time for item {item_id}: {e}")
                return None

    def get_users_with_items(self):
        with self.Session() as session:
            try:
                user_ids = session.query(TorobScrapUser.user_id).distinct().all()
                return [user_id[0] for user_id in user_ids]
            except Exception as e:
                print(f"get_all_user_id_of_oweners: {e}")
                return []


def add_dummy_data_for_testing():
    """
    Adds 21 rows of consistent, generated data to all tables for testing purposes.
    This function is for development and testing only and does not use the 'random' library.
    """
    # Generated data lists
    first_names = [
        "Jack",
        "Alice",
        "Bob",
        "Cynthia",
        "David",
        "Eva",
        "Frank",
        "Grace",
        "Henry",
        "Ivy",
        "John",
        "Kate",
        "Leo",
        "Mia",
        "Noah",
        "Olivia",
        "Peter",
        "Quinn",
        "Ryan",
        "Sarah",
        "Tom",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Jones",
        "Brown",
        "Davis",
        "Miller",
        "Wilson",
        "Moore",
        "Taylor",
        "Anderson",
        "Thomas",
        "Jackson",
        "White",
        "Harris",
        "Martin",
        "Thompson",
        "Garcia",
        "Martinez",
        "Robinson",
        "Clark",
    ]
    genders = ["male", "female"] * 11  # 11 male, 10 female to get 21
    cities = iran_cities_fa[:21]  # Use the first 21 cities from the provided list
    languages = ["en", "fa"] * 11

    # Initialize the database engine and session
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        try:
            # 1. Add 21 rows to 'users'
            dummy_users = []
            for i in range(21):
                user_id = 1000 + i
                user = User(
                    user_id=user_id,
                    generated_id=generate_secure_random_id(),
                    name=f"{first_names[i]} {last_names[i]}",
                    first_name=first_names[i],
                    last_name=last_names[i],
                    gender=genders[i],
                    age=20 + i,
                    city=cities[i],
                    last_online=datetime.now() - timedelta(minutes=i * 10),
                    about=f"About {first_names[i]}...",
                    latitude=35.6892 + i * 0.1,  # Generated sequential lat/long
                    longitude=51.3890 + i * 0.1,
                    language=languages[i],
                )
                dummy_users.append(user)
            session.add_all(dummy_users)
            session.commit()
            print("Added 21 rows of dummy data to 'users' table.")

            # 2. Add 21 rows to 'users_sessions'
            dummy_sessions = []
            for i in range(21):
                user_id = 1000 + i
                partner_id = 1000 + (i + 1) % 21  # Connects each user to the next one
                session_entry = Sessions(
                    user_id=user_id,
                    partner_id=partner_id,
                    secret_chat=(i % 2 == 0),
                    looking_random_chat=(i % 3 == 0),
                )
                dummy_sessions.append(session_entry)
            session.add_all(dummy_sessions)
            session.commit()
            print("Added 21 rows of dummy data to 'users_sessions' table.")

            # 3. Add 21 rows to 'relationships'
            dummy_relationships = []
            for i in range(21):
                user_id = 1000 + i
                target_id = (
                    1000 + (i + 2) % 21
                )  # Connects each user to a different user
                relationship = Relationships(
                    user_id=user_id,
                    target_id=target_id,
                    like=(i % 2 == 0),
                    friend=(i % 3 == 0),
                    block=(i % 4 == 0),
                    report=(i % 5 == 0),
                )
                dummy_relationships.append(relationship)
            session.add_all(dummy_relationships)
            session.commit()
            print("Added 21 rows of dummy data to 'relationships' table.")

            # 4. Add 21 rows to 'gold'
            dummy_gold_prices = []
            for i in range(21):
                gold_price_ir = 1500000 + i * 5000
                dollar_price_ir = 55000 + i * 100
                dummy_gold_prices.append(
                    GoldDollarRial(
                        gold_18k_ir=gold_price_ir,
                        dollar_ir_rial=dollar_price_ir,
                        time_check_ir=datetime.now() - timedelta(minutes=i),
                        gold_18k_international_dollar=1300 + i * 2,
                        gold_18k_international_rial=dollar_price_ir * (1300 + i * 2),
                        time_check_int=datetime.now() - timedelta(minutes=i),
                    )
                )
            session.add_all(dummy_gold_prices)
            session.commit()
            print("Added 21 rows of dummy data to 'gold' table.")

            # 5. Add 21 rows to 'torob_item'
            dummy_torob_items = []
            for i in range(21):
                user_id = 1000 + (i + 1) % 21  # Associate with existing dummy users
                item = TorobScrapUser(
                    user_id=user_id,
                    name_of_item=f"Laptop_{i}",
                    user_preferred_price=20000000 + i * 100000,
                    torob_url=f"http://example.com/torob_item/{i}",
                )
                dummy_torob_items.append(item)
            session.add_all(dummy_torob_items)
            session.commit()
            print("Added 21 rows of dummy data to 'torob_item' table.")

            # 6. Add 21 rows to 'torob_check'
            # We need the primary keys from torob_item first
            torob_items_from_db = session.query(TorobScrapUser).all()
            dummy_torob_checks = []
            for i, item in enumerate(torob_items_from_db):
                checked_price = item.user_preferred_price - (i * 1000)
                dummy_torob_checks.append(
                    TorobCheck(
                        item_id=item.item_id,
                        checked_price=checked_price,
                        check_timestamp=datetime.now() - timedelta(minutes=i),
                    )
                )
            session.add_all(dummy_torob_checks)
            session.commit()
            print("Added 21 rows of dummy data to 'torob_check' table.")

            # 7. Add 21 rows to 'message_map'
            dummy_messages = []
            for i in range(21):
                sender_id = 1000 + i
                receiver_id = 1000 + (i + 1) % 21
                message = MessageMap(
                    bot_message_id=50000 + i,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    msg_txt=f"Message {i + 1} from {first_names[i]}.",
                    requested=(i % 2 != 0),
                )
                dummy_messages.append(message)
            session.add_all(dummy_messages)
            session.commit()
            print("Added 21 rows of dummy data to 'message_map' table.")

            # 8. Add 21 rows to 'links'
            dummy_links = []
            for i in range(21):
                owner_id = 1000 + i
                link = Links(
                    link=generate_secure_random_id(12),
                    expire_time=datetime.now() + timedelta(days=30),
                    owner_id=owner_id,
                    max_uses=(i % 5) + 1,
                    number_of_used=i % 2,
                    active=(i % 2 == 0),
                )
                dummy_links.append(link)
            session.add_all(dummy_links)
            session.commit()
            print("Added 21 rows of dummy data to 'links' table.")

        except Exception as e:
            session.rollback()
            print(f"An error occurred while adding dummy data: {e}")
        finally:
            session.close()


if __name__ == "__main__":
    add_dummy_data_for_testing()
