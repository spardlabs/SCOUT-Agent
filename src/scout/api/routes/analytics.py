from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scout.api.deps import get_current_user, get_db
from scout.api.schemas.analytics import WeeklyReportListResponse, WeeklyReportResponse
from scout.db.models.analytics import WeeklyReport
from scout.db.models.user import User

router = APIRouter()


@router.get("/reports", response_model=WeeklyReportListResponse)
async def list_weekly_reports(
    skip: int = 0,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count()).select_from(WeeklyReport).where(WeeklyReport.user_id == user.id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.user_id == user.id)
        .order_by(WeeklyReport.week_start.desc())
        .offset(skip)
        .limit(limit)
    )
    reports = result.scalars().all()

    return WeeklyReportListResponse(
        reports=[WeeklyReportResponse.model_validate(r) for r in reports],
        total=total,
    )


@router.get("/reports/{report_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WeeklyReport).where(
            WeeklyReport.id == report_id,
            WeeklyReport.user_id == user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return WeeklyReportResponse.model_validate(report)
