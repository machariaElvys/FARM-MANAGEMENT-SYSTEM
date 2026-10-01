# Granting the first administrator account

Public registration always creates a farmer account. To grant administrator access, first create an account normally, then promote that account through the database provider's SQL console. Do not add an admin option to the public sign-up form.

For PostgreSQL, run this in the database SQL editor and replace the email with the exact account you registered:

```sql
UPDATE farmers
SET role = 'admin', is_active = TRUE
WHERE email = lower('admin@example.com')
RETURNING id, name, email, role;
```

Confirm that the returned row has `role = 'admin'`, then sign out and back in to refresh the frontend's user profile. The Admin page is visible only for that role, and the backend checks the role on every admin API request.

Current admin endpoints:

- `GET /api/admin/overview` — global account and record counts.
- `GET /api/admin/users` — paginated user list with name/email search and per-user record counts.
- `PATCH /api/admin/users/{user_id}/status` — suspend/reactivate a farmer account.

Administrator accounts cannot be suspended from this page. Change an administrator role only through a trusted database console.
