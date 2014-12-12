#!/bin/bash

execute="mysql -u root db_webcrawler -e"

echo 'Django only'
echo 'success by database'
$execute "select count(distinct(crawler_attempt.id))
from crawler_attempt
inner join crawler_dependency
on crawler_attempt.id = crawler_dependency.attempt_id
where crawler_attempt.result_id = 'Success'
and crawler_dependency.source_id = 'Database';"


sources=("File" "Database")
for sour in "${sources[@]}"
do
    echo "Number of all packages that installed from $sour when success"
    $execute "select count(distinct(crawler_dependency.package_id))
    from crawler_attempt
    inner join crawler_dependency
    on crawler_attempt.id = crawler_dependency.attempt_id
    where crawler_attempt.result_id = 'Success'
    and crawler_dependency.source_id = '$sour';"
done

echo 'diff Databaes - File'

$execute "select count(distinct(crawler_dependency.package_id))
from crawler_attempt
inner join crawler_dependency
on crawler_attempt.id = crawler_dependency.attempt_id
where crawler_attempt.result_id = 'Success'
and crawler_dependency.source_id = 'Database'
and crawler_dependency.package_id not in
(select crawler_dependency.package_id
from crawler_attempt
inner join crawler_dependency
on crawler_attempt.id = crawler_dependency.attempt_id
where crawler_attempt.result_id = 'Success'
and crawler_dependency.source_id = 'File');"


repo_types=("Django" "Ruby on Rails")
for repo_type in "${repo_types[@]}"
do
    echo $repo_type
    echo 'number crawled'
    $execute "select count(*)
    from crawler_repository
    where repo_type_id = '$repo_type';"

    echo 'number deployed'
    $execute "select count(*)
    from crawler_repository
    where repo_type_id = '$repo_type'
    and latest_attempt_id is not NULL;"

    echo 'number success'
    $execute "select count(*)
    from crawler_repository
    inner join crawler_attempt
    on crawler_repository.latest_attempt_id = crawler_attempt.id
    where crawler_repository.repo_type_id = '$repo_type'
    and crawler_attempt.result_id = 'Success';"

    echo 'database usage'
    $execute "select crawler_attempt.database_id, count(*)
    from crawler_repository
    inner join crawler_attempt
    on crawler_repository.latest_attempt_id = crawler_attempt.id
    where crawler_repository.repo_type_id = '$repo_type'
    group by crawler_attempt.database_id;"

    echo 'deployment result'
    $execute "select crawler_attempt.result_id, count(*)
    from crawler_repository
    inner join crawler_attempt
    on crawler_repository.latest_attempt_id = crawler_attempt.id
    where crawler_repository.repo_type_id = '$repo_type'
    group by crawler_attempt.result_id;"

    echo 'number of commits'
    $execute "select crawler_repository.commits_count
    into outfile '/tmp/$repo_type'
    from crawler_repository
    where crawler_repository.repo_type_id = '$repo_type';"

    echo 'number of commits of success'
    $execute "select crawler_repository.commits_count
    into outfile '/tmp/${repo_type}_success'
    from crawler_repository
    inner join crawler_attempt
    on crawler_repository.latest_attempt_id = crawler_attempt.id
    where crawler_repository.repo_type_id = '$repo_type'
    and crawler_attempt.result_id = 'Success';"
done


