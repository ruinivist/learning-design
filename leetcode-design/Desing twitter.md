# Design twitter

Couple things to keep in mind

- the get should do a priority queue push of latest from each user and then popping and
  replinishing as we go
- only maintain latest k posts via deque

```python
from collections import deque, defaultdict
import heapq


class Twitter:

    def __init__(self):
        # follow depth is just one
        # time will be a global counter ( in real world a timestamp )
        self.kFeedLimit = 10
        self.time = 0

        # userid to list of tweetids
        self.feedStore: dict[int, deque] = defaultdict(deque)
        self.follows: dict[int, set[int]] = defaultdict(set)

    def postTweet(self, userId: int, tweetId: int) -> None:
        # tweetId is expected unique
        userFeeds = self.feedStore[userId]
        userFeeds.append((self.time, tweetId))
        self.time += 1
        if len(userFeeds) > self.kFeedLimit:
            userFeeds.popleft()

    def getNewsFeed(self, userId: int) -> list[int]:
        # feed = my + my follower's posts ( top 10 )
        feed = []

        def tryAddPostFromUser(userId, index):
            posts = self.feedStore[userId]
            if index < 0 or index >= len(posts):
                return
            time, postId = posts[index]
            heapq.heappush(feed, (-time, postId, userId, index))

        sourceIds = (userId, *self.follows[userId])
        for srcId in sourceIds:
            tryAddPostFromUser(srcId, len(self.feedStore[srcId]) - 1)

        result = []
        while feed and len(result) < self.kFeedLimit:
            time, postId, userId, index = heapq.heappop(feed)
            result.append(postId)
            tryAddPostFromUser(userId, index - 1)

        return result

    def follow(self, followerId: int, followeeId: int) -> None:
        self.follows[followerId].add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self.follows[followerId].discard(followeeId)


# Your Twitter object will be instantiated and called as such:
# obj = Twitter()
# obj.postTweet(userId,tweetId)
# param_2 = obj.getNewsFeed(userId)
# obj.follow(followerId,followeeId)
# obj.unfollow(followerId,followeeId)
```
