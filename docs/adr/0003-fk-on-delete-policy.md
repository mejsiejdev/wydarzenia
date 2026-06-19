# Foreign-key ON DELETE policy: CASCADE for event-children, RESTRICT for user/location refs

The tables created in migration `54946b80e36b` (`events`, `event_access`,
`event_occurrences`, `event_registrations`) were created with no foreign keys at
all. Only `event_registrations` was later retrofitted (`359ac55e8401`). Migration
`a1f3c9d2e4b7` adds the remaining six FKs and three CHECK constraints, with a
deliberate `ON DELETE` policy:

- **CASCADE — references from an event-child to `events(id)`**:
  `event_access.event_id`, `event_occurrences.event_id`. Deleting an event removes
  its dependent rows; `event_access.user_id` also CASCADEs (deleting a grantee
  removes their access).
- **RESTRICT — references to `users(id)` and `locations(id)`**: `events.created_by`,
  `event_access.granted_by`, `event_occurrences.location_id`. These preserve
  history/audit — you cannot delete a user who still authored events or granted
  access, nor a location still referenced by an occurrence. `users` are
  hard-deleted (`routers/users.py`), so the delete endpoint now translates the
  resulting integrity error into `409 Conflict`. Locations are soft-deleted via
  `is_active`, so the location FK is a safety net.

CHECK constraints added at the same time: `event_occurrences.end_time >
start_time`, `room_availabilities.end_time > start_time`, and
`events.participant_limit >= 0`.

Chosen because CASCADE on event-children lets the hard-delete path drop its manual
ordered `DELETE`s, while RESTRICT on user/location references keeps the
history-preservation philosophy intact. RESTRICT was preferred over CASCADE (which
would wipe others' registrations when a creator is deleted) and over SET NULL
(which would orphan rows and require relaxing NOT NULL).

## Relationship to ADR 0001

This supersedes the FK reasoning in ADR 0001. ADR 0001 stated that the
`events_categories`, `event_blacklists`, `event_access`, and `event_occurrences`
foreign keys to `events(id)` had no `ON DELETE CASCADE` and were therefore wiped
manually on hard-delete. That was partly inaccurate: `event_access` and
`event_occurrences` had **no FK at all** until this migration. As of
`a1f3c9d2e4b7`, those two cascade automatically and their manual deletes were
removed from `routers/events.py`. The `events_categories` and `event_blacklists`
FKs remain `NO ACTION`, so their manual deletes stay. ADR 0001's soft-cancel
behavior (preserve history when registrations exist) is otherwise unchanged.
