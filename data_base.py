import time
from csv import excel
from time import sleep

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, select, inspect, ForeignKey, \
    Index, Boolean, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.horizontal_shard import set_shard_id
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from dolar_gold_price_ir import CheckSitePrice
from typing import Optional, Type, List
from sqlalchemy.sql import func
import os
import secrets
import string
import logging

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database/telegram_database.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path
#___________________________Web scarping Class_____________________________________________
site_checker_gold = CheckSitePrice()

Base = declarative_base()

#___________________________________________________________________________________________
def generate_secure_random_id(length=8):
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = ""

    # Combine all characters
    all_chars = lowercase + uppercase + digits + special

    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        # secrets.choice(special)
    ]

    # Fill the rest with random choices from all characters
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle the list to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    # Convert list to string
    return ''.join(password)


# Example usage

#___________________________________________________________________________________________
#_________________Initiate Users data base (for chat , etc, ..)_____________________________
#___________________________________________________________________________________________

class User(Base):
    __tablename__ = 'users'

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
    about = Column(Text, default='No bio yet', nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    registration_date = Column(DateTime, default=datetime.now, nullable=True)



#todo neeed new tables for likes manaager 1 to many and list of who like who
#todo need new friendship table 1 to many it should request accept and both side
#todo need new block list 1 to many and need a check to stop some actions from block users
#todo need a report list
#___________________________________________________________________________________________
#____________________________Initiate Gold & Dollar data base ______________________________
#___________________________________________________________________________________________

class GoldDollarRial(Base):
    __tablename__ = "gold"

    check_id = Column(Integer, primary_key=True)
    gold_18k_ir = Column(Float, nullable=False)
    dollar_ir_rial = Column(Float, nullable=False)
    time_check_ir = Column(DateTime, nullable=False)
    gold_18k_international_dollar = Column(Float, nullable=False)
    gold_18k_international_rial = Column(Float, nullable=False)
    time_check_int = Column(DateTime, nullable=False)

#___________________________________________________________________________________________
#____________________________Initiate Gold & Dollar data base ______________________________
#___________________________________________________________________________________________

class TorobScrapUser(Base):
    __tablename__ = "torob_item"

    item_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name_of_item = Column(String, nullable=False)
    user_preferred_price = Column(Float, nullable=False)
    torob_url = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())  # Database timestamp
    updated_at = Column(DateTime, onupdate=func.now())
    price_checks = relationship(
        'TorobCheck',
        back_populates='item',
        cascade="all, delete-orphan"
    )


class TorobCheck(Base):
    __tablename__ = "torob_check"

    check_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('torob_item.item_id'))
    checked_price = Column(Float, nullable=False)
    check_timestamp = Column(DateTime, server_default=func.now())


    item = relationship(
        'TorobScrapUser',
        back_populates='price_checks'
    )

#___________________________________________________________________________________________
#_____________________________Initiate Users Chat data base ________________________________
#___________________________________________________________________________________________

class Sessions(Base):
    __tablename__ = 'users_sessions'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)

    partner_id = Column(Integer, nullable=True)
    perv_partner_id = Column(Integer, nullable=True)
    secret_chat = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())  # Database timestamp
    updated_at = Column(DateTime, onupdate=func.now())
    looking_random_chat = Column(Boolean, default=False)

    # Relationship to messages where this user is the sender
    sent_messages = relationship(
        'MessageMap',
        foreign_keys="[MessageMap.sender_id]",
        back_populates='sender'
    )
    # Relationship to messages where this user is the receiver
    received_messages = relationship(
        'MessageMap',
        foreign_keys="[MessageMap.receiver_id]",
        back_populates='receiver'
    )
    links = relationship(
        'Links',
        foreign_keys='[Links.owner_id]',
        back_populates='owner'
    )
    __table_args__ = (
        Index('idx_partner', 'partner_id'),
    )
#___________________________________________________________________________________________
#_____________________________Initiate Users Message Map data base ________________________________
#___________________________________________________________________________________________

class MessageMap(Base):
    __tablename__ = 'message_map'

    message_id = Column(Integer, primary_key=True)
    bot_message_id = Column(Integer, nullable=False)
    sender_id = Column(Integer, ForeignKey('users_sessions.user_id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users_sessions.user_id') ,nullable=False)
    time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    msg_txt = Column(String, nullable=True)
    requested = Column(Boolean, nullable=True)

    # Relationship to the sender (Sessions)
    sender = relationship(
        'Sessions',
        foreign_keys=[sender_id],
        back_populates='sent_messages'
    )
    # Relationship to the receiver (Sessions)
    receiver = relationship(
        'Sessions',
        foreign_keys=[receiver_id],
        back_populates='received_messages'
    )

    # Recommended indexes
    __table_args__ = (
        # Composite index for finding conversations between two users
        Index('idx_conversation', 'sender_id', 'receiver_id'),

        # Reverse composite index for the same conversation
        Index('idx_conversation_reverse', 'receiver_id', 'sender_id'),

        # Index for time-based queries (message history)
        Index('idx_message_time', 'time'),

        # Index for bot message tracking (if you query by bot_message_id)
        Index('idx_bot_message', 'bot_message_id'),
    )


#___________________________________________________________________________________________
#_____________________________Initiate Users Links data base ________________________________
#___________________________________________________________________________________________

class Links(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    link = Column(String, unique=True)
    expire_time = Column(DateTime, nullable=False)
    owner_id = Column(Integer, ForeignKey('users_sessions.user_id'))
    max_uses = Column(Integer, nullable=True)
    number_of_used = Column(Integer, nullable=True, default=0)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship back to owner (corrected)
    owner = relationship(
        'Sessions',
        back_populates='links',  # Matches Sessions.links
        foreign_keys=[owner_id],
    )
    __table_args__ = (
        Index('idx_link_active', 'link', 'active'),
        Index('idx_owner_link', 'owner_id', 'link'),
    )



#___________________________________________________________________________________________
#____________________________Class of Gold & Dollar data base ______________________________
#___________________________________________________________________________________________

#todo merge two table in one db put them in a folder
class GoldPriceDatabase:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.on_check = None

#________________________________adding new price to the db manually________________________

    def add_price(self, gold_18k_ir, dollar_ir_rial, time_check_ir,
                  gold_18k_international_dollar,
                  gold_18k_international_rial,
                  time_check_int):
        session = self.Session()
        check = GoldDollarRial(
            gold_18k_ir = gold_18k_ir,
            dollar_ir_rial = dollar_ir_rial,
            time_check_ir = time_check_ir,
            gold_18k_international_dollar = gold_18k_international_dollar,
            gold_18k_international_rial = gold_18k_international_rial,
            time_check_int = time_check_int,
        )
        session.add(check)
        session.commit()
        session.close()

#________________________________Getting latest update from db_______________________________
#todo this may not return get back any should be handled i think
    def get_latest_price(self):
        session = self.Session()
        try:
            return session.query(GoldDollarRial).order_by(GoldDollarRial.check_id.desc()).first()
        finally:
            session.close()
    #todo is it better to get request from here or the main how is time managed
#___________________Checking latest ir update from db (validate_time)__________________________
    def latest_ir_update(self, validate_time=600):
        latest_check = self.get_latest_price()
        if latest_check:
            latest_ir_check = latest_check.time_check_ir
            difference = datetime.now() - latest_ir_check
            if difference.seconds > validate_time:
                return True
        else:
            return True
#___________________Checking latest int update from db (validate_time)__________________________
    def latest_int_update(self, validate_time=600):
        latest_check = self.get_latest_price()
        if latest_check:
            latest_int_check = latest_check.time_check_int
            difference  = datetime.now() - latest_int_check

            if difference.seconds > validate_time:
                return True
        else:
            return True
#________combine of all top function to check time valide and chose from where to update_________
    # todo when it is checking take mins other users dont make request again and get from db or tell to wait
    def get_latest_update(self):
        latest_check = self.get_latest_price()

        # If another check is in progress, wait and return the cached data
        if self.on_check:
            logging.info("Another update is in progress. Returning the latest cached price.")
            time.sleep(2)
            return latest_check  # return cached/latest instead of risky recursion

        self.on_check = True
        try:
            # Check if Iranian site needs update
            if not self.latest_ir_update():
                # Check if International site also needs update
                if not self.latest_int_update():
                    logging.info("Both IR and INT data are up-to-date in DB. No need to fetch.")
                    pass  # Both are fine, use DB value
                else:
                    # Only INT site needs update, IR is valid from DB
                    try:
                        logging.info("Fetching INT site data only.")
                        gold_18k_ir = latest_check.gold_18k_ir
                        dollar_ir = latest_check.dollar_ir_rial
                        time_check_ir = latest_check.time_check_ir

                        gold_18k_int_dlr, gold_18k_int_rial, check_time_int = site_checker_gold.get_int_gold_to_dollar_to_rial(
                            price_dollar_rial=dollar_ir
                        )

                        self.add_price(
                            float(gold_18k_ir.replace(",", "")),
                            float(dollar_ir.replace(",", "")),
                            time_check_ir,
                            float(gold_18k_int_dlr),
                            float(gold_18k_int_rial),
                            check_time_int
                        )
                    except Exception as e:
                        logging.error(f"Error fetching INT site data: {e}")
            else:
                # Both need updating from the sites
                try:
                    logging.info("Fetching both IR and INT site data.")
                    gold_18k_ir, dollar_ir, time_check_ir = site_checker_gold.get_ir_gold_dollar()
                    gold_18k_int_dlr, gold_18k_int_rial, check_time_int = site_checker_gold.get_int_gold_to_dollar_to_rial(
                        price_dollar_rial=dollar_ir
                    )

                    self.add_price(
                        float(gold_18k_ir.replace(",", "")),
                        float(dollar_ir.replace(",", "")),
                        time_check_ir,
                        float(gold_18k_int_dlr),
                        float(gold_18k_int_rial),
                        check_time_int
                    )
                except Exception as e:
                    logging.error(f"Error fetching both IR and INT site data: {e}")

        finally:
            self.on_check = False  # Always release the lock

        return self.get_latest_price()





# ___________________________________________________________________________________________
# ________________________________Class of Users data base __________________________________
# ___________________________________________________________________________________________
            #todo from here??!! check what did i ment
            #todo ah lets start heree for filters and things
            #todo read it carefully

class UserDatabase:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)




    def get_user_data(self, user_id, user_data):
        session = self.Session()

        user = session.query(User).filter_by(user_id=str(user_id)).first()

        if not user:
            user = User(user_id=str(user_id))
            user.registration_date = datetime.now()

        inspector = inspect(user)
        for column in inspector.mapper.column_attrs:
            column_name = column.key
            column_value = getattr(user, column_name)
            user_data[column_name] = column_value

        session.add(user)
        session.commit()
        session.close()

    def generate_user_special_id(self, max_attempts=25):
        """
        Generates a unique special ID for new users.

        Args:
            max_attempts (int): Maximum number of generation attempts before failing

        Returns:
            str: A unique generated ID

        Raises:
            RuntimeError: If unable to generate a unique ID after max_attempts
        """
        attempt = 0

        while attempt < max_attempts:
            generated_id = generate_secure_random_id()

            try:
                with self.Session() as session:
                    # More efficient exists query - stops at first match
                    exists = session.query(
                        session.query(User)
                        .filter_by(generated_id=generated_id)
                        .exists()
                    ).scalar()

                    if not exists:
                        return generated_id

                    attempt += 1

            except Exception as e:
                print(f'Error generating user ID (attempt {attempt + 1}): {e}')
                attempt += 1
                continue

        raise RuntimeError(
            f"Failed to generate unique ID after {max_attempts} attempts"
        )

    def get_user_information(self, target_id:int) ->Optional[User]:
        """
        search a user with provided id and return data
        :param target_id: id of target
        :return: data of user if not exist return None
        """
        with self.Session() as session:
            try:
                user = session.query(User).filter_by(user_id=str(target_id)).first()
                return user
            except Exception as e:
                logging.error(f"Database error fetching user {target_id}: {e}")
                return None


    def add_or_update_user(self, user_id, user_data):
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=str(user_id)).first()

            if not user:
                generated_id = self.generate_user_special_id()
                user = User(user_id=str(user_id), generated_id=generated_id)
                user.registration_date = datetime.now()
                user_data['generated_id'] = generated_id
            if not self.get_user_generated_id(user_id):
                generated_id = self.generate_user_special_id()
                user_data['generated_id'] = generated_id



            if not user_data:
                user_data = {}
            generated_id = user_data.get('generated_id', "")
            # for before update ppl
            if not generated_id:

                user_data['generated_id'] = self.get_user_generated_id(user_id)


            # Update all fields

            for key, value in user_data.items():

                if hasattr(user, key):
                    setattr(user, key, value)

            user.last_online = datetime.now()
            session.add(user)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_users(self):
        session = self.Session()
        try:
            return session.query(User).order_by(User.last_online.desc()).all()
        finally:
            session.close()

    def get_users_online_time(self, time_min:int):
        with self.Session() as session:
            time_threshold = datetime.now() - timedelta(minutes=time_min)
            query = select(User).where(User.last_online >= time_threshold).order_by(User.last_online.desc())
            return session.execute(query).scalars().all()

    def get_users_location(self,user_id, max_km=9999999.0):

        with self.Session() as session:
            # 1. Get the requesting user's location
            requesting_user = session.get(User, user_id)
            if not requesting_user or not requesting_user.latitude:
                return []

            # 2. Get all users (or better: filter nearby users directly in SQL)
            all_users = session.query(User).filter(
                User.latitude.isnot(None),
                User.longitude.isnot(None),
                User.user_id != requesting_user.user_id  # Exclude self
            ).all()

            # 3. Calculate distances and online status
            now = datetime.now()
            nearby_users = []

            for user in all_users:
                distance = self._calculate_distance(
                    requesting_user.latitude, requesting_user.longitude,
                    user.latitude, user.longitude
                )

                if distance <= max_km:
                    # Calculate minutes since last online
                    mins_ago = (now - user.last_online).total_seconds() / 60
                    is_online = mins_ago <= 1  # Consider online if active in last 1 minute

                    nearby_users.append({
                        'user': user,
                        'distance': distance,
                        'mins_ago': mins_ago,
                        'is_online': is_online
                    })


            # 4. Sort by: online status first, then by minutes ago, then by distance
            return sorted(
                nearby_users,
                key=lambda x: (
                    not x['is_online'],  # Online users first (False sorts before True)
                    x['mins_ago'],  # Then by minutes since online
                    x['distance']  # Then by distance
                )
            )

    def get_filtered_users(self, user_data):
        """
        Returns filtered users with additional calculated fields.

        Args:
            user_data (dict): Should contain:
                - user_id: The requesting user's ID
                - user_filter: Dictionary of filter criteria including:
                    - dis_filter: Max distance in km
                    - last_online_filter: Max minutes since last online
                    - gender_filter: List of genders to include
                    - age_filter: [min_age, max_age] or [exact_age]
                    - city_filter: List of cities to include

        Returns:
            List[dict]: Each containing user data with additional fields:
                - user: User object
                - distance: Distance from requesting user
                - mins_ago: Minutes since last online
                - is_online: Boolean if user is currently online
        """
        try:
            # Validate input
            if not isinstance(user_data, dict):
                raise ValueError("user_data must be a dictionary")

            user_id = str(user_data.get('user_id', ""))
            if not user_id:
                raise ValueError("user_id is required")

            # Update/create the requesting user's record
            self.add_or_update_user(user_id, user_data)
            self.get_user_data(user_id, user_data)

            # Get initial user set with location data
            selected_users = self.get_users_location(user_id)
            if not selected_users:
                return []

            user_filters = user_data.get('user_filter', {})

            # Apply filters sequentially
            if 'dis_filter' in user_filters and user_filters['dis_filter']:
                try:
                    max_dis = float(user_filters['dis_filter'])
                    selected_users = [u for u in selected_users if u['distance'] <= max_dis]
                except (ValueError, TypeError):
                    pass  # Skip invalid distance filter

            if 'last_online_filter' in user_filters and user_filters['last_online_filter']:
                try:
                    max_mins = int(user_filters['last_online_filter'])
                    selected_users = [u for u in selected_users if u['mins_ago'] <= max_mins]
                except (ValueError, TypeError):
                    pass

            if 'gender_filter' in user_filters and user_filters['gender_filter']:
                gender_filter = [g.lower() for g in user_filters['gender_filter']]
                selected_users = [
                    u for u in selected_users
                    if u['user'].gender and u['user'].gender.lower() in gender_filter
                ]

            if 'age_filter' in user_filters and user_filters['age_filter']:
                try:
                    age_filter = user_filters['age_filter']
                    if len(age_filter) == 2:
                        min_age, max_age = age_filter
                        selected_users = [
                            u for u in selected_users
                            if u['user'].age and min_age <= u['user'].age <= max_age
                        ]
                    elif len(age_filter) == 1:
                        selected_users = [
                            u for u in selected_users
                            if u['user'].age and u['user'].age == age_filter[0]
                        ]
                except (ValueError, TypeError):
                    pass

            if 'city_filter' in user_filters and user_filters['city_filter']:
                city_filter = user_filters['city_filter']
                selected_users = [
                    u for u in selected_users
                    if u['user'].city and u['user'].city in city_filter
                ]

            return selected_users

        except Exception as e:
            print(f"Error in get_filtered_users: {str(e)}")
            return []

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):

        R = 6371

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
            user_id: The integer user ID to look up

        Returns:
            The generated ID string if found, None otherwise

        Example:
            generated_id = await get_user_generated_id(12345)
            if generated_id:
                print(f"Found ID: {generated_id}")
        """
        try:
            with self.Session() as session:
                # Using scalar() for single-value queries is more efficient
                generated_id = session.execute(
                    select(User.generated_id).where(User.user_id == user_id)
                ).scalar()
                if generated_id:
                    return generated_id if generated_id else None

        except SQLAlchemyError as e:
            #logger.error(f"Database error fetching generated ID for user {user_id}: {e}",
            print(f"Error fetching generated ID for user {user_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in get_user_generated_id: {e}")
            return None

    def get_user_id_from_generated_id(self, generated_id):
        """
                Retrieves the user ID  for a user based on their system-generated ID.

                Args:
                    generated_id: The integer user Generated ID to look up

                Returns:
                    The User ID string if found, None otherwise

                Example:
                    generated_id = await get_user_generated_id(12345)
                    if generated_id:
                        print(f"Found ID: {generated_id}")
                """
        try:
            with self.Session() as session:
                # Using scalar() for single-value queries is more efficient
                user_id = session.execute(
                    select(User.user_id).where(User.generated_id == generated_id)
                ).scalar()
                if user_id:
                    return user_id if user_id else None

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
    "قزوین"
]


# ___________________________________________________________________________________________
# ________________________________Class of Users Chat base __________________________________
# ___________________________________________________________________________________________

class ChatDatabase:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def reset_db(self):
        """reset the db for early development only"""
        with self.engine.connect() as conn:
            conn.execute(text("ALTER TABLE message_map ADD COLUMN msg_txt TEXT"))
            conn.commit()
    #todo this should be activate each intract of user with bot
    def create_user_session(self, user_id: int):
        """insure user has added to the session db"""
        with self.Session() as session:
            if not session.query(Sessions).filter_by(user_id=user_id).first():
                new_session = Sessions(user_id=user_id)
                session.add(new_session)
                session.commit()
    def add_partner(self, user_id:int, partner_id: int) -> bool:
        """add a partner for user users.

           Args:
               user_id: ID of the first user
               partner_id: ID of the second user

           Returns:
               bool: True if added as partner, False if:
                     - Either user doesn't exist
                     - Users are already partners
                     - Database error occurs
           """
        with self.Session() as session:
            try:
                # Verify both users exist
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()
                user2 = session.query(Sessions).filter_by(user_id=partner_id).first()

                if not user1 or not user2:
                    return False

                # Check if already partners
                if user1.partner_id == partner_id :
                    return True  # Already partners

                # Establish mutual partnership
                user1.partner_id = partner_id
                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error adding partner {partner_id}: {e}")
                return False
    def remove_partner(self, user_id: int) -> bool:
        """remove partner of user.

    Args:
        user_id: ID of the user

    Returns:
        bool: True if users partner removed, False if:
              - Either user doesn't exist
              - Users are not partners
              - Database error occurs
    """
        with self.Session() as session:
            try:
                # Verify both users exist
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()

                if not user1 :
                    return False
                # Check if already partners
                user1.partner_id = None
                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error removing partner of {user_id} : {e}")
                return False

    def set_partnership(self, user_id: int, partner_id: int) -> bool:
        """Establish a mutual partnership between two users.

    Args:
        user_id: ID of the first user
        partner_id: ID of the second user

    Returns:
        bool: True if partnership was successfully established, False if:
              - Either user doesn't exist
              - Users are already partners
              - Database error occurs
    """
        with self.Session() as session:
            try:
                # Verify both users exist
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()
                user2 = session.query(Sessions).filter_by(user_id=partner_id).first()

                if not user1 or not user2:
                    return False

                # Check if already partners
                if user1.partner_id == partner_id and user2.partner_id == user_id:
                    return True  # Already partners

                # Establish mutual partnership
                user1.partner_id = partner_id
                user2.partner_id = user_id
                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error establishing partnership between {user_id} and {partner_id}: {e}")
                return False

    def remove_partnership(self, user_id: int) -> bool:
        """remove a mutual partnership between two users.

    Args:
        user_id: ID of the first user

    Returns:
        bool: True if partnership was successfully breaked, False if:
              - Either user doesn't exist
              - Users are not partners
              - Database error occurs
    """
        with self.Session() as session:
            try:
                # Verify both users exist
                user1 = session.query(Sessions).filter_by(user_id=user_id).first()
                partner_id = user1.partner_id
                user2 = session.query(Sessions).filter_by(user_id=partner_id).first()

                if not user1 or not user2:
                    return False

                # Check if already partners
                if user1.partner_id == partner_id:
                    user1.perv_partner_id = user1.partner_id
                    user1.partner_id = None
                if user2.partner_id == user_id:
                    user2.perv_partner_id = user2.partner_id
                    user2.partner_id = None
                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error establishing partnership between {user_id} and other person: {e}")
                return False

    def get_user_session(self, user_id:int) -> Optional[Sessions]:
        """Retrieve a user's session by their ID.

            Args:
                user_id: The ID of the user whose session to retrieve

            Returns:
                Optional[Sessions]: The session object if found, None otherwise
            """
        with self.Session() as session:
            try:
                return session.query(Sessions
                                     ).filter_by(user_id=user_id
                                                 ).first()
            except Exception as e:
                print(f"Error fetching session for user {user_id}: {e}")
                return None

    def get_partner_id(self, user_id: int) -> Optional[int]:
        try:
            session_obj = self.get_user_session(user_id)
            if session_obj:
                return session_obj.partner_id
            else:
                print(f'No session found for user {user_id} when trying to get partner ID.')
                return None
        except Exception as e:
            print(f'Could not get partner id: {e}')
            return None
    def cleanup_expired_links(self):
        with self.Session() as session:
            try:
                session.query(Links).filter(
                    Links.expire_time < datetime.now()
                ).update({'active': False})
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error cleaning links: {e}")
    def add_link(self,
                 link:str,
                 user_id:int,
                 exp_time_hr:int=24,
                 max_uses:Optional[int]= None
                 ) -> Optional[Links]:
        """Adds a new link/token to the database.

                Args:
                    link (str): Unique token/link identifier.
                    user_id (int): User ID who owns the link.
                    exp_time_hr (int): Expiration time in hours (default: 24).
                    max_uses (Optional[int]): Max allowed uses. None = unlimited (default).

                Returns:
                    Links: The created link object, or None if failed.
                """
        self.cleanup_expired_links()
        with self.Session() as session:
            # Verify the user_id exists in users_sessions
            if not session.query(Sessions).filter_by(user_id=user_id).first():
                raise ValueError(f"User {user_id} has no session!")
            try:
                new_link = Links(
                    link=link,
                    owner_id=str(user_id),
                    expire_time=datetime.now() + timedelta(hours=exp_time_hr),
                    max_uses = max_uses
                )


                session.add(new_link)
                session.commit()
                return new_link
            except Exception as e:
                session.rollback()
                print(f'Failed to add link: {e}')
                return None

    def get_link(self, link:str) -> Optional[Links]:
        """Retrieve a link by its token if it exists and is not expired."""
        self.cleanup_expired_links()

        with self.Session() as session:
            try:
                link_obj = session.query(Links).filter(
                    Links.link == link,
                    Links.active == True,
                    Links.expire_time >= datetime.now()
                ).first()
                return link_obj
            except Exception as e:
                print(f"Error fetching link: {e}")
                return None

    def get_link_owner(self, link: str) -> Optional[int]:
        self.cleanup_expired_links()

        link_obj = self.get_link(link)  # Reuse existing method
        return link_obj.owner_id if link_obj else None



    #todo badan havasam bashe number of use handle shode bashe
    #todo decrement_link_use nemishe too get link bashe?
    def decrement_link_use(self, link:str)-> bool:
        """Decrement remaining uses of a link. Returns True if successful.

            Args:
                link: The link token to decrement uses for

            Returns:
                bool: True if decrement was successful, False if:
                      - Link doesn't exist
                      - Link is expired
                      - Link has no remaining uses
            """
        with self.Session() as session:
            link_obj = session.query(Links).filter_by(link=link).first()
            if not link_obj:
                return False
            if link_obj.expire_time <= datetime.now():
                link_obj.active = False
                session.commit()
                return False
            if link_obj.max_uses is not None:
                if link_obj.max_uses <= 0:
                    link_obj.active = False
                    session.commit()
                    return False

                link_obj.max_uses -= 1
            link_obj.number_of_used += 1
            session.commit()
            return True

    def get_msg_id_by_robot_msg(self, robot_msg_id:int) -> Optional[int]:
        """Get the internal message ID associated with a bot message ID.

            Args:
                robot_msg_id: The bot's message ID to look up

            Returns:
                Optional[int]: The internal message ID if found, None otherwise
            """
        with self.Session() as session:
            try:
                msg_obj = session.query(MessageMap
                                        ).filter_by(bot_message_id=robot_msg_id
                                                    ).first()
                return msg_obj.message_id if msg_obj else None
            except Exception as e:
                print(f"Error fetching message for bot message: {robot_msg_id}: {e}")
                return None
    def get_msg_id_by_user_msg(self, user_msg_id:int) -> Optional[int]:
        """Get the internal message ID associated with a user message ID.

            Args:
                user_msg_id: The bot's message ID to look up

            Returns:
                Optional[int]: The internal message ID if found, None otherwise
            """
        with self.Session() as session:
            try:
                msg_obj = session.query(MessageMap
                                        ).filter_by(message_id=user_msg_id
                                                    ).first()
                return msg_obj.bot_message_id if msg_obj else None
            except Exception as e:
                print(f"Error fetching message for bot message: {user_msg_id}: {e}")
                return None

    def map_message(self, user_msg, bot_msg, user_id, partner_id, msg_txt=None) -> bool:
        """Mapping internal messages between users witch handled by bot
        Args:
            user_msg: id of message user sent
            bot_msg: id of message bot sent to partner
            user_id: id of user who sent message
            partner_id: id of user who receive message
            msg_txt: adds the text of msg

        Returns:
            True: if mapped
            False: if could not map
        """
        new_msg = MessageMap(
            message_id = user_msg,
            bot_message_id = bot_msg,
            sender_id = user_id,
            receiver_id= partner_id,
            time= datetime.now(),
            msg_txt=msg_txt
        )
        try:
            with self.Session() as session:
                session.add(new_msg)
                session.commit()
                return True
        except Exception as e:
            print(f"Could not map message with message id: {user_msg} : {e}")
            return False


    def secret_chat_toggle(self, user_id:int, hand_change:Optional[bool]=None):
        """Toggle or set the secret chat status for a user.

    Args:
        user_id: ID of the user to modify
        hand_change: If None, toggles current state. If bool, sets directly.

    Returns:
        bool: True if successful, False if error or user not found
    """
        with self.Session() as session:
            try:

                session_obj = session.query(Sessions).filter_by(user_id=user_id).first()
                if not session_obj:
                    print(f'no session found for user {user_id}')
                    return False
                session_obj.secret_chat = not session_obj.secret_chat if hand_change is None else hand_change

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                print(f"Error toggling secret chat for user {user_id}: {e}")
                return False
    def get_user_messages(self, user_id:int)-> Optional[List[MessageMap]]:
        """
        get all the users messages from map
        :param user_id: id of user registered on bot
        :return: if it has msg on map all of them order by time if not None
        """
        with self.Session() as session:
            try:
                messages = session.query(MessageMap
                                         ).filter(MessageMap.sender_id == user_id
                                                  ).order_by(MessageMap.time.desc()
                                                             ).all()
                return messages if messages else None
            except Exception as e:
                print(f'Error fetching messages for user {user_id}: {str(e)}')
                return None

    def get_previous_partner_messages(self, user_id: int, perv_partner_id: int) -> Optional[List[MessageMap]]:
        """get chats of two partner after leaving chat
        Args:
            user_id: id of user
            perv_partner_id: id of user who was in chat with user
        Return:
            bool: True if success and False if unsuccessful
        """
        with self.Session() as session:
            try:
                messages = session.query(MessageMap
                                         ).filter((MessageMap.sender_id == user_id),
                                                    (MessageMap.receiver_id == perv_partner_id)
                                                  ).order_by(MessageMap.time.desc()
                                                             ).all()
                return messages if messages else None
            except Exception as e:
                print(f'Error fetching messages for user {user_id}: {str(e)}')
                return None
    def clear_msg_map(self, exp_time: Optional[int] = None, user_id: Optional[int] = None):
        """
        Clears message_map entries based on expiration time and/or user_id.

        Args:
            exp_time: Hours before now to delete older messages
            user_id: Delete messages where user is sender or receiver

        Returns:
            tuple: (deleted_count, error_message)
        """
        if not exp_time and not user_id:
            return (0, "Please provide either exp_time or user_id")

        deleted_count = 0
        with self.Session() as session:
            try:
                query = session.query(MessageMap)

                # Build filters
                # inja nabayad request bashe check she ke doroste
                filters = [MessageMap.requested == False]



                if exp_time:
                    time_threshold = datetime.now() - timedelta(hours=exp_time)
                    filters.append(MessageMap.time <= time_threshold)
                if user_id:
                    filters.append(
                        (MessageMap.sender_id == user_id) |
                        (MessageMap.receiver_id == user_id)
                    )



                # Execute deletion in single operation
                if filters:
                    deleted_count = query.filter(*filters).delete()
                    session.commit()

                return (deleted_count, None)

            except Exception as e:
                session.rollback()
                error_msg = f"Error clearing message_map: {str(e)}"
                print(error_msg)
                return (0, error_msg)
    def set_random_chat(self, user_id:int, stat:bool) -> bool:
        """
        set users looking for random chat status
        :param user_id: id of the user
        :param stat: True if looking false if not looking
        :return: True if it is successful Fale if it is not
        """
        with self.Session() as session:
            try:
                user_session = session.query(Sessions).filter_by(user_id=user_id).first()
                if not user_session:
                    print(f"User session not found for {user_id}")
                    return False
                user_session.looking_random_chat = stat
                session.commit()

                # Verify the change
                session.refresh(user_session)
                print(f"Updated status for {user_id}: {user_session.looking_random_chat}")
                return True
            except Exception as e:
                print(f'Could not change random chat statuse : {e}')
                return False

    def get_random_chaters(self, female=True, male=True) -> list:
        """
        Get all users looking for random chat based on gender filters.

        Args:
            female (bool): Include female users.
            male (bool): Include male users.

        Returns:
            list: List of User objects matching the gender filter.
        """
        with self.Session() as session:
            try:
                random_users = session.query(Sessions, User) \
                    .join(User, Sessions.user_id == User.user_id) \
                    .filter(Sessions.looking_random_chat == True) \
                    .all()

                result = []
                print(random_users)
                for session_obj, user in random_users:
                    if user.gender and user.gender.lower() == 'male':
                        if male:  # Include male users if requested
                            result.append(user)
                    elif user.gender and user.gender.lower() == 'female':
                        if female:  # Include female users if requested
                            result.append(user)
                    else:
                        if not male and not female:  # Include 'other' only if both male and female are False
                            result.append(user)

                return result

            except Exception as e:
                print(f"Error getting random chatters: {e}")
                return []
    def get_msg_requests_from_map(self, user_id:int, sender_id:int) -> Optional[List[Column[str]]]:
        """
        try to return list of text of requested msgs
        :param user_id: number
        :param sender_id: number
        :return: a list of requested msg
        """
        with self.Session() as session:
            try:
                messages = session.query(MessageMap).filter_by(receiver_id=user_id,
                                                                sender_id=sender_id,
                                                                requested=True).all()
                texts = [msg.msg_txt for msg in messages]
                for msg in messages:
                    msg.requested = False
                session.commit()

                return texts
            except Exception as e:
                print(f'Could not get request msgs : {e}')
                return None
    def clear_msg_requests_from_map(self, user_id:int, sender_id:int) -> bool:
        """
        try to delete list of text of requested msgs
        :param user_id: number
        :param sender_id: number
        :return: True if deleted else false
        """
        with self.Session() as session:
            try:
                messages = session.query(MessageMap).filter_by(receiver_id=user_id,
                                                               sender_id=sender_id,
                                                               requested=True).all()

                for msg in messages:
                    session.delete(msg)
                    session.commit()

                return True
            except Exception as e:
                print(f'Could not get request msgs : {e}')
                return False
    def add_requested_msg(self, sender_id, receiver_id, msg_txt)->bool:
        with self.Session() as session:
            #todo bot_msg_id should be none and nullable in the table
            try:
                new_msg = MessageMap(
                    bot_message_id=6969,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    msg_txt=msg_txt,
                    requested=True,
                    time=datetime.now()
                )
                session.add(new_msg)
                session.commit()
                return True
            except Exception as e:
                print(f'error in adding new request msg: {e}')
                return False


#todo user can has a current name for setuation he is in like anom goes with unknown person
class TorobDb:
    def __init__(self):
        self.engine=create_engine(SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_item(self, user_id:int, preferred_price:float, torob_url:str, name:Optional[str]) -> bool:
        """

        :param user_id: id of who wants the scrap
        :param preferred_price: highest price the person need it to be
        :param torob_url: url of the item in torob site
        :param name: name of item
        :return: True if item added, False if it did not add
        """
        with self.Session() as session:
            try:
                new_torob = TorobScrapUser(
                    user_id = user_id,
                    name_of_item = name,
                    user_preferred_price = preferred_price,
                    torob_url = torob_url,
                )
                session.add(new_torob)
                session.commit()
                return True
            except Exception as e:
                print(f'Failed to add item: {e}')
                return False

    def add_check(self, item_id:int, checked_price:float) -> bool:
        """
        adding new check to database
        :param item_id: id of item we checked
        :param checked_price: price of item at this timee
        :return: True if added to db, False if it could not add to db
        """

        try:
            with self.Session() as session:
                new_check = TorobCheck(
                    item_id=item_id,
                    checked_price=checked_price
                )
                session.add(new_check)
                session.commit()
                return True
        except Exception as e:
            print(f"could not added the check: {e}")
            return False

    def get_user_items(self, user_id: int) -> List[Type[TorobScrapUser]]:
        """
        Retrieves a list of all items tracked by a specific user.
        :param user_id: The ID of the user whose items are to be retrieved.
        :return: A list of TorobScrapUser objects. Returns an empty list if no items are found or on error.
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

    def check_ownership(self, user_id:int, item_id:int)->bool:
        """
        checks check the item id owner be the user
        :param user_id: id of user
        :param item_id: id of item
        :return: True if this user is the owner of this item and False if it is not
        """
        try:
            user_items = self.get_user_items(user_id)
            if user_items:
                user_items_id = [item.item_id for item in user_items]
                if item_id in user_items_id:
                    return True
                else:
                    print('he/she is not the owner')
                    return False
            else:
                print('user do not has any item yet')
                return False
        except Exception as e:
            print(f'about checking item owner this happend : {e}')
            return False
    def update_preferred_price(self, item_id: int, new_price: float) -> bool:
        """
        Updates the user's preferred price for a specific item.
        :param item_id: The ID of the item to update.
        :param new_price: The new preferred price.
        :return: True if the price was updated successfully, False otherwise (e.g., item not found).
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
                session.rollback() # Rollback in case of error
                print(f"Failed to update preferred price for item {item_id}: {e}")
                return False

    def update_url(self, item_id: int, new_url: str) -> bool:
        """
        Updates the URL for a specific item.

        :param item_id: The ID of the item to update.
        :param new_url: The new URL for the item.
        :return: True if the URL was updated successfully, False otherwise (e.g., item not found).
        """
        with self.Session() as session:
            try:
                # Find the item by its primary key
                item_to_update = session.query(TorobScrapUser).get(item_id)

                if item_to_update:
                    # Validate URL format if needed
                    if not new_url.startswith(('http://', 'https://')):
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

        :param item_id: The ID of the item to update.
        :param new_name: The new name for the item.
        :return: True if the name was updated successfully, False otherwise (e.g., item not found).
        """
        with self.Session() as session:
            try:
                # Find the item by its primary key
                item_to_update = session.query(TorobScrapUser).get(item_id)

                if item_to_update:
                    # Validate name length if needed
                    if len(new_name) > 150:  # Assuming 150 char limit
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
        :param item_id: The ID of the item whose price history is to be retrieved.
        :return: A list of TorobCheck objects, ordered by check_timestamp. Returns an empty list if no checks are found or on error.
        """
        with self.Session() as session:
            try:
                # Query for TorobCheck objects filtered by item_id
                # .order_by(TorobCheck.check_timestamp) ensures the history is chronological
                # .all() executes the query
                price_history = session.query(TorobCheck).filter_by(item_id=item_id).order_by(
                    TorobCheck.check_timestamp).all()
                return price_history
            except Exception as e:
                print(f"Failed to retrieve price history for item {item_id}: {e}")
                return []

    def get_item_by_id(self, item_id: int) -> Optional[TorobScrapUser]:
        """
        Retrieves a single TorobScrapUser item by its primary key.
        :param item_id: The ID of the item to retrieve.
        :return: The TorobScrapUser object if found, None otherwise.
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
        Deletes a TorobScrapUser item and its associated price checks.
        Requires 'cascade="all, delete-orphan"' on the relationship.
        :param item_id: The ID of the item to delete.
        :return: True if deleted, False otherwise (e.g., item not found).
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
                session.rollback()
                print(f"Failed to delete item {item_id}: {e}")
                return False

    def get_latest_price(self, item_id: int) -> Optional[float]:
        """
        Retrieves the most recent checked price for a given item.
        :param item_id: The ID of the item.
        :return: The latest checked price as a float, or None if no checks exist for the item.
        """
        with self.Session() as session:
            try:
                # Query for the latest check by item_id, order by timestamp descending, and take the first one.
                latest_check = session.query(TorobCheck) \
                    .filter_by(item_id=item_id) \
                    .order_by(TorobCheck.check_timestamp.desc()) \
                    .first()
                return latest_check.checked_price if latest_check else None
            except Exception as e:
                print(f"Failed to get latest price for item {item_id}: {e}")
                return None

    def get_latest_check(self, item_id: int) -> Optional[DateTime]:
        """
        Retrieves the most recent checked price for a given item.
        :param item_id: The ID of the item.
        :return: The latest checked price as a float, or None if no checks exist for the item.
        """
        with self.Session() as session:
            try:
                # Query for the latest check by item_id, order by timestamp descending, and take the first one.
                latest_check = session.query(TorobCheck) \
                    .filter_by(item_id=item_id) \
                    .order_by(TorobCheck.check_timestamp.desc()) \
                    .first()
                return latest_check.check_timestamp if latest_check else None
            except Exception as e:
                print(f"Failed to get latest check time for item {item_id}: {e}")
                return None
