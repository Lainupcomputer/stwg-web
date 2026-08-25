from . import db
from datetime import datetime


def current_time():
    return datetime.now().strftime("%d.%m.%Y %H:%M")


class JetpackHighscore(db.Model):

    __tablename__ = "jetpack_highscores"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    user_id = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True
    )


    username = db.Column(
        db.String(100),
        nullable=False
    )


    highscore = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )


    games_played = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )


class InternalDocument(db.Model):
    __tablename__ = "internal_documents"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class WaspHighscore(db.Model):
    __tablename__ = "wasp_highscores"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.String(32),
        nullable=False,
        unique=True
    )

    username = db.Column(
        db.String(255),
        nullable=False
    )

    highscore = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    games_played = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "highscore": self.highscore,
            "games_played": self.games_played,
            "created_at": self.created_at.isoformat()
                if self.created_at else None,
            "updated_at": self.updated_at.isoformat()
                if self.updated_at else None
        }


class VoiceCreditChannel(db.Model):
    __tablename__ = "voice_credit_channels"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    guild_id = db.Column(
        db.BigInteger,
        nullable=False,
        index=True
    )

    channel_id = db.Column(
        db.BigInteger,
        nullable=False,
        unique=True,
        index=True
    )

    channel_name = db.Column(
        db.String(255),
        nullable=False
    )

    credit_rate = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<VoiceCreditChannel "
            f"{self.channel_id} "
            f"{self.channel_name}>"
        )


class TeamMeeting(db.Model):
    __tablename__ = "team_meetings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    meeting_date = db.Column(
        db.Date,
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.now,
        nullable=False
    )


class StatusMessage(db.Model):
    __tablename__ = "status_messages"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    message = db.Column(
        db.String(200),
        nullable=False
    )


class RuleField(db.Model):
    __tablename__ = "rule_fields"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    title = db.Column(
        db.String(100),
        nullable=False
    )

    content = db.Column(
        db.String(2000),
        nullable=False
    )

    inline = db.Column(
        db.Boolean,
        default=False
    )


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.BigInteger,
        unique=True,
        index=True
    )

    username = db.Column(
        db.String(100)
    )

    status = db.Column(
        db.String(16)
    )

    join_date = db.Column(
        db.String(50),
        default="current_time"
    )

    last_uprank = db.Column(
        db.String(50),
        default="null"
    )

    comments = db.relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    warnings = db.relationship(
        "Warning",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    group_actions = db.relationship(
        "GroupAction",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    currency_total = db.Column(
        db.Integer
    )

    currency_month = db.Column(
        db.Integer,
        default=0
    )

    has_payed = db.Column(
        db.Boolean,
        default=False
    )

    is_member = db.Column(
        db.Boolean,
        default=False
    )

    awards = db.Column(
        db.TEXT
    )

    licenses = db.Column(
        db.TEXT
    )


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user_profiles.user_id")
    )

    author = db.Column(
        db.String(100)
    )

    comment = db.Column(
        db.String(1000)
    )

    user = db.relationship(
        "UserProfile",
        back_populates="comments"
    )


class Warning(db.Model):
    __tablename__ = "warnings"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user_profiles.user_id")
    )

    time = db.Column(
        db.String(50),
        default=current_time()
    )

    comment = db.Column(
        db.String(1000)
    )

    user = db.relationship(
        "UserProfile",
        back_populates="warnings"
    )


class GroupAction(db.Model):
    __tablename__ = "group_actions"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("user_profiles.user_id")
    )

    time = db.Column(
        db.String(50),
        default=current_time()
    )

    action = db.Column(
        db.String(1000)
    )

    user = db.relationship(
        "UserProfile",
        back_populates="group_actions"
    )


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    creator_id = db.Column(
        db.String(64),
        nullable=False
    )

    creator_name = db.Column(
        db.String(64),
        nullable=False
    )

    handler_id = db.Column(
        db.String(64),
        nullable=True
    )

    description = db.Column(
        db.String(1024),
        nullable=True
    )

    status = db.Column(
        db.String(24),
        nullable=False,
        default="open"
    )

    created_at = db.Column(
        db.String(50),
        default=current_time()
    )

    closed_at = db.Column(
        db.String(50),
        nullable=True
    )

    is_locked = db.Column(
        db.String(50),
        default=False
    )

    channel_id = db.Column(
        db.String(40),
        nullable=True
    )

    transcript = db.Column(
        db.Text,
        nullable=True
    )


class DataStorage(db.Model):
    __tablename__ = "data_storage"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    key = db.Column(
        db.String(1024)
    )

    data = db.Column(
        db.String(1024)
    )


class ActionQueue(db.Model):
    __tablename__ = "action_queue"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    key = db.Column(
        db.String(1024)
    )

    data = db.Column(
        db.JSON()
    )

    timestamp = db.Column(
        db.String(50),
        default=current_time()
    )


class MessagePreset(db.Model):
    __tablename__ = "message_presets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    type = db.Column(
        db.String(50)
    )

    title = db.Column(
        db.String(100)
    )

    text = db.Column(
        db.Text
    )

    def as_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "text": self.text
        }


class DMMessage(db.Model):
    __tablename__ = "dm_messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.BigInteger
    )

    user_name = db.Column(
        db.String(256)
    )

    text = db.Column(
        db.String(1024)
    )

    date = db.Column(
        db.String(50),
        default=current_time()
    )

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "text": self.text,
            "date": self.date
        }


class WarehouseItem(db.Model):
    __tablename__ = "warehouse_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    weight = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )


class Warehouse(db.Model):
    __tablename__ = "web_warehouse"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.BigInteger,
        nullable=False
    )

    user_name = db.Column(
        db.String(100),
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("warehouse_items.id"),
        nullable=False
    )

    amount = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    item_data = db.relationship(
        "WarehouseItem",
        backref="warehouse_entries"
    )


class MarketItem(db.Model):
    __tablename__ = "market_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    display_name = db.Column(
        db.String(150),
        nullable=False
    )

    min_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    base_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    max_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0
    )

    enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    history = db.relationship(
        "MarketPriceHistory",
        backref="item",
        lazy=True,
        cascade="all, delete-orphan"
    )

    external_id = db.Column(
        db.Integer,
        unique=True,
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<MarketItem {self.name}>"


class MarketPriceHistory(db.Model):
    __tablename__ = "market_price_history"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("market_items.id"),
        nullable=False,
        index=True
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<MarketPriceHistory {self.item_id}: {self.price}>"


class MarketAlert(db.Model):
    __tablename__ = "market_alerts"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("market_items.id"),
        nullable=False,
        index=True
    )

    condition = db.Column(
        db.String(1),
        nullable=False
    )

    target_price = db.Column(
        db.Float,
        nullable=False
    )

    enabled = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    armed = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    last_price = db.Column(
        db.Float,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    item = db.relationship(
        "MarketItem",
        backref=db.backref(
            "market_alerts",
            lazy=True
        )
    )


class Training(db.Model):
    __tablename__ = "trainings"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.Text,
        nullable=False,
        default=""
    )

    document = db.Column(
        db.Text,
        nullable=True
    )

    required_monthly = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    completions = db.relationship(
        "TrainingCompletion",
        back_populates="training",
        cascade="all, delete-orphan"
    )


class TrainingCompletion(db.Model):
    __tablename__ = "training_completions"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    # Interne ID aus user_profiles.id
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user_profiles.id"),
        nullable=False,
        index=True
    )

    training_id = db.Column(
        db.Integer,
        db.ForeignKey("trainings.id"),
        nullable=False,
        index=True
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    month = db.Column(
        db.Integer,
        nullable=False
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    trainer_id = db.Column(
        db.BigInteger,
        nullable=True
    )

    trainer_name = db.Column(
        db.String(255),
        nullable=True
    )

    note = db.Column(
        db.Text,
        nullable=True
    )

    user = db.relationship(
        "UserProfile",
        backref=db.backref(
            "training_completions",
            lazy=True
        )
    )

    training = db.relationship(
        "Training",
        back_populates="completions"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "training_id",
            "year",
            "month",
            name="uq_training_user_month"
        ),
    )