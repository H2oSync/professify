\set A '''{"sub":"aaaaaaaa-0000-0000-0000-000000000001","role":"authenticated","email":"a@calpoly.edu"}'''
begin; set local role authenticated; set local request.jwt.claims = :A;
select assistant_log_run('0123456789abcdef','q','help','{}'::jsonb,null,null,null,null,null,null,false,false,'NaN');
select assistant_log_run('0123456789abcdef','q','help','{}'::jsonb,null,null,null,null,null,null,false,false,999);
reset role; select usd from assistant_spend; rollback;
