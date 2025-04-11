async def get_post_info(
        blog_id: int,
        session: AsyncSession = SessionDep,
        user_data: User | None = Depends(get_current_user_optional)
) -> BlogFullResponse | BlogNotFind:
    author_id = user_data.id if user_data else None
    return await BlogDAO.get_full_blog_info(session=session, blog_id=blog_id, author_id=author_id)
