from rest_framework.throttling import UserRateThrottle


class ProjectScanRateThrottle(UserRateThrottle):
    scope = "project_scan"


class SnapshotRateThrottle(UserRateThrottle):
    scope = "snapshots"


class NotificationRateThrottle(UserRateThrottle):
    scope = "notifications"


class InfrastructureCheckRateThrottle(UserRateThrottle):
    scope = "infrastructure_checks"
