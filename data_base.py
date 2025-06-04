from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, select, inspect, ForeignKey, \
    Index, Boolean, text
from sqlalchemy.ext.horizontal_shard import set_shard_id
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from dolar_gold_price_ir import CheckSitePrice
from typing import Optional, Type, List
from sqlalchemy.sql import func
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database/telegram_database.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + db_path
#___________________________Web scarping Class_____________________________________________
site_checker_gold = CheckSitePrice()

Base = declarative_base()
#___________________________________________________________________________________________
#_________________Initiate Users data base (for chat , etc, ..)_____________________________
#___________________________________________________________________________________________

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
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

class TorobScrap(Base):
    __tablename__ = "torob"

    check_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name_of_item = Column(String, nullable=True)
    time_check_ir = Column(DateTime, nullable=True)
    item_price = Column(Float, nullable=True)
    user_preferred_price = Column(Float, nullable=False)
    torob_url = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())  # Database timestamp
    updated_at = Column(DateTime, onupdate=func.now())

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
        latest_ir_check = latest_check.time_check_ir
        difference = datetime.now() - latest_ir_check
        if difference.seconds > validate_time:
            return True

#___________________Checking latest int update from db (validate_time)__________________________
    def latest_int_update(self, validate_time=600):
        latest_check = self.get_latest_price()
        latest_int_check = latest_check.time_check_int
        difference  = datetime.now() - latest_int_check
        if difference.seconds > validate_time:
            return True
#________combine of all top function to check time valide and chose from where to update_________
    # todo when it is checking take mins other users dont make request again and get from db or tell to wait
    def get_latest_update(self):
        #this looks overkill check again
        latest_check = self.get_latest_price()
        #if both site or not past long time should update from db

        if not self.latest_ir_update():
            if not self.latest_int_update():
                pass


            # if int site or not past valid time but ir site did should int update from db and ir update from site
            # this looks kinda overkill, but it will use full if we have two Different validator for time
            else:
                gold_18k_ir = latest_check.gold_18k_ir
                dollar_ir = latest_check.dollar_ir_rial
                time_check_ir = latest_check.time_check_ir
                gold_18k_int_dlr, gold_18k_int_rial, check_time_int = site_checker_gold.get_int_gold_to_dollar_to_rial(
                    price_dollar_rial=dollar_ir)
                self.add_price(float(gold_18k_ir.replace(",", "")), float(dollar_ir.replace(",", "")), time_check_ir,
                              float(gold_18k_int_dlr),
                              float(gold_18k_int_rial),
                              check_time_int)


        #if both need to be updated from sites
        else:
            gold_18k_ir, dollar_ir, time_check_ir = site_checker_gold.get_ir_gold_dollar()
            gold_18k_int_dlr, gold_18k_int_rial, check_time_int = site_checker_gold.get_int_gold_to_dollar_to_rial(
                price_dollar_rial=dollar_ir)
            self.add_price(float(gold_18k_ir.replace(",", "")), float(dollar_ir.replace(",", "")), time_check_ir,
                           float(gold_18k_int_dlr),
                           float(gold_18k_int_rial),
                           check_time_int)


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



    def add_or_update_user(self, user_id, user_data):
        session = self.Session()

        user = session.query(User).filter_by(user_id=str(user_id)).first()

        if not user:
            user = User(user_id=str(user_id))
            user.registration_date = datetime.now()

        if not user_data:
            user_data = {}
        # Update all fields
        for key, value in user_data.items():

            if hasattr(user, key):
                setattr(user, key, value)

        user.last_online = datetime.now()
        session.add(user)
        session.commit()
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
        """" return a list of dict from users witch one has the data of db with key of user
         and included some extra data as distance, mins_ago, is_online(boolean) """

        #todo this user_id should be not there
        self.add_or_update_user(user_data['user_id'], user_data)
        selected_users = self.get_users_location(user_data['user_id'])
        user_filters = user_data['user_filter']

        if 'dis_filter' in user_filters and user_filters['dis_filter'] != "":
            # load_profile
            max_dis = float(user_filters['dis_filter'])
            print(selected_users)

            selected_users = [data for data in selected_users if max_dis >= data['distance']]
            print([f"{data['user'].name}: {data['distance']}" for data in selected_users])

        if 'last_online_filter' in user_filters and user_filters['last_online_filter'] != "":
            time_now = datetime.now()
            selected_users = [data for data in selected_users if
                         data['mins_ago'] <= user_filters['last_online_filter']]
            print([f"{data['user'].name}: {data['mins_ago']}" for data in selected_users])

        if 'gender_filter' in user_filters and user_filters['gender_filter'] != []:
            selected_users = [data for data in selected_users if data['user'].gender.lower() in user_filters['gender_filter']]
            print([f"{data['user'].name}:{data['user'].gender}" for data in selected_users])

        if 'age_filter' in user_filters and user_filters['age_filter'] != []:
            if len(user_filters['age_filter']) == 2:
                min_age = user_filters['age_filter'][0]
                max_age = user_filters['age_filter'][1]
                selected_users = [data for data in selected_users if min_age <= data['user'].age <= max_age]
            elif len(user_filters['age_filter']) == 1:
                selected_users = [data for data in selected_users if data['user'].age == user_filters['age_filter'][0]]
            print([f"{data['user'].name}:{data['user'].age}" for data in selected_users])

        if 'city_filter' in user_filters and user_filters['city_filter'] != []:
            selected_users = [data for data in selected_users if data['user'].city in user_filters['city_filter']]
            print([f"{data['user'].name}:{data['user'].city}" for data in selected_users])

        return selected_users

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
                filters = []
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
                new_torobi = TorobScrap(
                    user_id = user_id,
                    name_of_item = name,
                    user_preferred_price = preferred_price,
                    torob_url = torob_url,
                )
                session.add(new_torobi)
                session.commit()
                return True
            except Exception as e:
                print(f'Failed to add item: {e}')
                return False
