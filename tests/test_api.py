from httpx import AsyncClient


async def test_create_first_user(async_client: AsyncClient):
    """ Создание тестового пользователя """
    response = await async_client.post(
        "/users/",
        json={
            "fullname": "I am FIRST TEST USER",
            "user_id": "FIRST TEST USER",
        },
    )

    assert response.status_code == 200


async def test_create_second_user(async_client: AsyncClient):
    """ Создание второго тестового пользователя """
    response = await async_client.post(
        "/users/",
        json={
            "fullname": "I am SECOND TEST USER",
            "user_id": "SECOND TEST USER",
        },
    )

    assert response.status_code == 200


async def test_create_first_task(async_client: AsyncClient):
    """ Создание тестовой задачи для первого пользователя """
    response = await async_client.post(
        "/tasks/create_task",
        json={
            "task_id": "TEST first USER TASK",
            "description": "This is test user task",
            "owner_id": 1,
            "activity": "00:00",
        },
    )

    assert response.status_code == 200


async def test_create_second_task(async_client: AsyncClient):
    """ Создание тестовой задачи для второго пользователя """
    response = await async_client.post(
        "/tasks/create_task",
        json={
            "task_id": "TEST second USER TASK",
            "description": "This is test second user task",
            "owner_id": 2,
            "activity": "00:00",
        },
    )

    assert response.status_code == 200


async def test_get_all_tasks(async_client: AsyncClient):
    """ Получение задач всех пользователей"""
    response = await async_client.get("/tasks/")

    assert response.status_code == 200
    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == [
        {
            'activity': '00:00',
            "task_id": "TEST first USER TASK",
            "description": "This is test user task",
            "owner_id": 1,
            'id': 1,
        },
        {
            'activity': '00:00',
            "task_id": "TEST second USER TASK",
            "description": "This is test second user task",
            "owner_id": 2,
            'id': 2,
        },
    ]


async def test_create_first_timeline(async_client: AsyncClient):
    """ Создание первого таймлайна """
    response = await async_client.post(
        "/timelines/create_new_timeline",
        json={
            "task_id": 1,
            "owner_id": 1,
            "description": "THIS IS TEST TIMELINES",
            "time_start": "2024-06-17 12:44",
            "time_end": "2024-06-17 17:44",
        },
    )

    assert response.status_code == 200


async def test_create_second_timeline(async_client: AsyncClient):
    response = await async_client.post(
        "/timelines/create_new_timeline",
        json={
            "task_id": 2,
            "owner_id": 2,
            "description": "THIS IS TEST TIMELINES FOR SECOND USER",
            "time_start": "2024-06-17 13:21",
            "time_end": "2024-06-17 16:19",
        },
    )

    assert response.status_code == 200


async def test_get_timeline(async_client: AsyncClient):
    """ Получение таймлайна """
    response = await async_client.get(
        "/timelines/",
    )

    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == [
        {
            "id": 1,
            "task_id": 1,
            "owner_id": 1,
            "description": "THIS IS TEST TIMELINES",
            "time_start": "2024-06-17T12:44:00",
            "time_end": "2024-06-17T17:44:00",
            "activity": "05:00",
        },
        {
            "id": 2,
            "task_id": 2,
            "owner_id": 2,
            "description": "THIS IS TEST TIMELINES FOR SECOND USER",
            "time_start": "2024-06-17T13:21:00",
            "time_end": "2024-06-17T16:19:00",
            "activity": "02:58",
        },
    ]


async def test_get_all_tasks_after_add_timeline(async_client: AsyncClient):
    """ Получение всех задач после добавления таймлайна """
    response = await async_client.get("/tasks/")

    assert response.status_code == 200
    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == [
        {
            "id": 1,
            "task_id": "TEST first USER TASK",
            "description": "This is test user task",
            "owner_id": 1,
            "activity": "05:00",
        },
        {
            "id": 2,
            "task_id": "TEST second USER TASK",
            "description": "This is test second user task",
            "owner_id": 2,
            "activity": "02:58",
        },
    ]


async def test_get_timelines_for_specified_user(async_client: AsyncClient):
    """ Получение таймлайнов для конкретного пользователя  """
    response = await async_client.post(
        "/timelines/get_timelines_for_specified_user",
        json={
            "time_start": "2024-06-17 00:00",
            "time_end": "2024-06-17 21:00",
            "user_id": 1,
        },
    )

    assert response.status_code == 200
    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == [
        {
            "id": 1,
            "task_id": 1,
            "owner_id": 1,
            "description": "THIS IS TEST TIMELINES",
            "time_start": "2024-06-17T12:44:00",
            "time_end": "2024-06-17T17:44:00",
            "activity": "05:00",
        },
    ]


async def test_get_timelines_for_second_specified_user(
    async_client: AsyncClient,
):
    """ Получение таймлайнов для второго пользователя  """
    response = await async_client.post(
        "/timelines/get_timelines_for_specified_user",
        json={
            "time_start": "2024-06-17 00:00",
            "time_end": "2024-06-17 21:00",
            "user_id": 2,
        },
    )

    assert response.status_code == 200
    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == [
        {
            "id": 2,
            "task_id": 2,
            "owner_id": 2,
            "description": "THIS IS TEST TIMELINES FOR SECOND USER",
            "time_start": "2024-06-17T13:21:00",
            "time_end": "2024-06-17T16:19:00",
            "activity": "02:58",
        },
    ]


async def test_get_summary_activity_for_first_user(async_client: AsyncClient):
    """ Получение суммарной активности для конкретного пользователя  """
    response = await async_client.post(
        "/timelines/get_summary_timeline_for_specified_user",
        json={
            "time_start": "2024-06-14 00:00",
            "time_end": "2024-06-17 21:00",
            "user_id": 1,
        },
    )

    assert response.status_code == 200
    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == {
        "user_id": 1,
        "summary": {"hours": 5, "minutes": 0},
    }


async def test_get_summary_activity_for_second_user(async_client: AsyncClient):
    """ Получение суммарной активности для второго пользователя  """
    response = await async_client.post(
        "/timelines/get_summary_timeline_for_specified_user",
        json={
            "time_start": "2024-06-14 00:00",
            "time_end": "2024-06-17 21:00",
            "user_id": 2,
        },
    )

    assert response.status_code == 200
    deserialized_response = response.json()
    assert len(deserialized_response) != 0
    assert deserialized_response == {
        "user_id": 2,
        "summary": {"hours": 2, "minutes": 58},
    }


async def test_get_downtime_and_timeline_for_specified_user(
    async_client: AsyncClient,
):
    """ Получение времени простоев для первого пользователя  """
    response = await async_client.post(
        "/timelines/get_downtime_and_timeline_for_specified_user",
        json={
            "time_start": "2024-06-17",
            "time_end": "2024-06-17",
            "user_id": 1,
            "time_start_work": "09:00",
            "time_end_work": "18:00",
        },
    )

    assert response.status_code == 200
    deserialized_response = response.json()
    assert deserialized_response == {
        "2024-06-17": [
            {
                "task_id": "EXECUTABLE TASK NOT FOUND!",
                "owner_id": 1,
                "description": "DOWNTIME",
                "time_start": "2024-06-17T09:00:00",
                "time_end": "2024-06-17T12:44:00",
                "activity": "03:44",
            },
            {
                "time_start": "2024-06-17T12:44:00",
                "task_id": 1,
                "activity": "05:00",
                "description": "THIS IS TEST TIMELINES",
                "time_end": "2024-06-17T17:44:00",
                "owner_id": 1,
                "id": 1,
            },
            {
                "task_id": "EXECUTABLE TASK NOT FOUND!",
                "owner_id": 1,
                "description": "DOWNTIME",
                "time_start": "2024-06-17T17:44:00",
                "time_end": "2024-06-17T18:00:00",
                "activity": "00:16",
            },
        ]
    }


async def test_delete_first_user(async_client: AsyncClient):
    """ Удаление первого пользователя """
    response = await async_client.delete(
       "/users/1",
    )

    assert response.status_code == 200


async def test_delete_second_user(async_client: AsyncClient):
    """ Удаление второго пользователя """
    response = await async_client.delete(
        "/users/2",
    )
    assert response.status_code == 200


async def test_get_timeline_after_all_cascade_delete(async_client: AsyncClient):
    """ Получение таймлайнов после касскадного удаления """
    response = await async_client.get(
        "/timelines/",
    )

    deserialized_response = response.json()
    assert deserialized_response == []


# TODO Добавить формирование проверки незавершенных timeline-ов
# async def test_create_unfinished_timeline(async_client: AsyncClient):tests/test_api.py::test_get_timeline
#     response = await async_client.post(
#         "/timelines/create_new_timeline",
#         json={
#             "id": 2,
#             "task_id": 2222,
#             "owner_id": 1111,
#             "description": "THIS IS TEST TIMELINES",
#             "time_start": "2024-06-17 12:44",
#             "time_end": "2024-06-17 --:--",
#             "activity": "00:00",
#         },
#     )

#     assert response.status_code == 200


# async def test_create_finish_unfinished_timeline(async_client: AsyncClient):
#     response = await async_client.post(
#         "/timelines/create_new_timeline",
#         json={
#             "id": 2,
#         },
#     )

#     assert response.status_code == 200
