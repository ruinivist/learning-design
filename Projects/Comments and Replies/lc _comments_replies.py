import time
import threading
from dataclasses import dataclass, replace

# ==== impl summary ====
# The impl itself ios simple, we define dataclasses with their serailisation
# helpers. The state is just a comments by post dict. Locking is broad as well
# In my initial impl I sorted the ids but in python dicts iteration is based on
# insertion order so no need to sort


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


@dataclass(frozen=True)
class Reply:
    id: int
    post_id: int
    comment_id: int
    user_id: str
    content: str
    created_at: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "comment_id": self.comment_id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class Comment:
    id: int
    post_id: int
    user_id: str
    content: str
    created_at: float
    replies: tuple[Reply, ...] = ()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "content": self.content,
            "created_at": self.created_at,
            "replies": [reply.to_dict() for reply in self.replies],
        }


class CommentService:
    def __init__(self, post_store):
        self.post_store = post_store
        self.next_comment_id = 1
        self.next_reply_id = 1
        self.comments_by_post = {}
        self.lock = threading.Lock()

    def now_seconds(self) -> float:
        return time.time()

    def _is_valid_text(self, value):
        return isinstance(value, str) and len(value.strip()) > 0

    def add_comment(self, post_id: int, user_id: str, content: str) -> dict:
        """
        Create a comment and return its dictionary representation.

        Raises NotFoundError if post_id does not exist.
        Raises ValidationError if user_id or content is empty.
        """
        if not self._is_valid_text(user_id) or not self._is_valid_text(content):
            raise ValidationError()

        with self.lock:
            if not self.post_store.exists(post_id):
                raise NotFoundError()

            comment = Comment(
                id=self.next_comment_id,
                post_id=post_id,
                user_id=user_id,
                content=content,
                created_at=self.now_seconds(),
            )

            self.comments_by_post.setdefault(post_id, {})
            self.comments_by_post[post_id][comment.id] = comment
            self.next_comment_id += 1

        return comment.to_dict()

    def add_reply(
        self, post_id: int, comment_id: int, user_id: str, content: str
    ) -> dict:
        """
        Create a reply to a comment and return its dictionary representation.

        Raises NotFoundError if post_id does not exist.
        Raises NotFoundError if comment_id does not exist for the given post.
        Raises ValidationError if user_id or content is empty.
        """
        if not self._is_valid_text(user_id) or not self._is_valid_text(content):
            raise ValidationError()

        with self.lock:
            if not self.post_store.exists(post_id):
                raise NotFoundError()

            post_comments = self.comments_by_post.get(post_id)

            if post_comments is None or comment_id not in post_comments:
                raise NotFoundError()

            comment = post_comments[comment_id]

            reply = Reply(
                id=self.next_reply_id,
                post_id=post_id,
                comment_id=comment_id,
                user_id=user_id,
                content=content,
                created_at=self.now_seconds(),
            )

            post_comments[comment_id] = replace(
                comment, replies=comment.replies + (reply,)
            )

            self.next_reply_id += 1

        return reply.to_dict()

    def get_comments(self, post_id: int) -> list:
        """
        Return all comments for the given post.

        Each comment includes its replies.
        Comments and replies are returned in creation order.

        Raises NotFoundError if post_id does not exist.
        """
        with self.lock:
            if not self.post_store.exists(post_id):
                raise NotFoundError()

            snapshot = tuple(self.comments_by_post.get(post_id, {}).values())

        return [comment.to_dict() for comment in snapshot]
