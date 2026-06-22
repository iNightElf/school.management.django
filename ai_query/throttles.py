from rest_framework.throttling import UserRateThrottle


class AIQueryRateThrottle(UserRateThrottle):
    scope = 'ai_query'
