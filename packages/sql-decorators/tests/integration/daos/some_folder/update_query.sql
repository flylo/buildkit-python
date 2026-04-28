UPDATE test
SET some_number = COALESCE(:new_number, some_number)
WHERE some_string = :search_string
RETURNING *;
