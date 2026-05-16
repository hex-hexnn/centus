from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, List

from django.db.models import Sum
from django.utils import timezone

from .models import Transaction, BudgetLimit, Subscription


@dataclass
class Recommendation:
    level: str   # "info" | "warning" | "success"
    title: str
    message: str


def month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def next_month_start(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


def money(x) -> str:
    # Bezpieczne formatowanie kwot
    if x is None:
        x = Decimal("0")
    return f"{x:.2f} PLN"


def get_savings_recommendations(user, for_month: Optional[date] = None) -> List[dict]:
    """
    Generuje rekomendacje oszczędnościowe dla użytkownika na podstawie transakcji,
    limitów i subskrypcji dla wybranego miesiąca.
    Zwraca listę słowników: {level, title, message} (łatwe do template).
    """
    today = timezone.localdate()
    target = for_month or today
    start = month_start(target)
    end = next_month_start(start)

    recs: list[Recommendation] = []

    # --- Dane bazowe: transakcje miesiąca ---
    qs = Transaction.objects.filter(user=user, date__gte=start, date__lt=end)

    income = (qs.filter(category__type="INCOME").aggregate(s=Sum("amount"))["s"] or Decimal("0"))
    expense = (qs.filter(category__type="EXPENSE").aggregate(s=Sum("amount"))["s"] or Decimal("0"))
    balance = income - expense

    recs.append(Recommendation(
        level="info",
        title="Podsumowanie miesiąca",
        message=f"Przychody: {money(income)} • Wydatki: {money(expense)} • Bilans: {money(balance)}"
    ))

    if expense == 0:
        recs.append(Recommendation(
            level="warning",
            title="Brak wydatków",
            message="Nie masz jeszcze wydatków w tym miesiącu. Dodaj transakcje, aby Centuś mógł wygenerować konkretne porady."
        ))
        # nadal pokażemy subskrypcje/limity, jeśli istnieją
    else:
        # Prosty wskaźnik oszczędzania
        if income > 0:
            savings_rate = (balance / income) * Decimal("100")
            if savings_rate < 0:
                recs.append(Recommendation(
                    level="warning",
                    title="Bilans na minusie",
                    message="W tym miesiącu wydatki przewyższają przychody. Spróbuj ograniczyć największą kategorię wydatków lub ustaw limity."
                ))
            elif savings_rate < 10:
                recs.append(Recommendation(
                    level="warning",
                    title="Niski poziom oszczędności",
                    message=f"Oszczędzasz ok. {savings_rate:.1f}% przychodu. Cel 10–20% miesięcznie często jest osiągalny po ograniczeniu 1–2 kategorii."
                ))
            else:
                recs.append(Recommendation(
                    level="success",
                    title="Dobra kontrola budżetu",
                    message=f"Oszczędzasz ok. {savings_rate:.1f}% przychodu. Tak trzymaj — warto utrzymać trend."
                ))

        # --- TOP kategorie wydatków ---
        top = (
            qs.filter(category__type="EXPENSE")
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:3]
        )

        if top:
            lines = [f"• {row['category__name']}: {money(row['total'])}" for row in top]
            recs.append(Recommendation(
                level="info",
                title="Największe kategorie wydatków",
                message="Najwięcej wydajesz na:\n" + "\n".join(lines)
            ))

            # Heurystyka: podpowiedź na największą kategorię
            biggest = top[0]
            recs.append(Recommendation(
                level="warning",
                title=f"Sugestia: ogranicz {biggest['category__name']}",
                message=f"To Twoja największa kategoria wydatków ({money(biggest['total'])}). Spróbuj obniżyć ją o 5–10% w kolejnym miesiącu."
            ))

    # --- Limity budżetowe (BudgetLimit) ---
    limits = BudgetLimit.objects.filter(user=user, month=start).select_related("category")
    if limits.exists():
        for lim in limits:
            spent = (
                qs.filter(category=lim.category, category__type="EXPENSE")
                .aggregate(s=Sum("amount"))["s"] or Decimal("0")
            )
            if lim.limit_amount > 0:
                ratio = spent / lim.limit_amount
            else:
                ratio = Decimal("0")

            if ratio >= Decimal("1.0"):
                recs.append(Recommendation(
                    level="warning",
                    title=f"Limit przekroczony: {lim.category.name}",
                    message=f"Wydano {money(spent)} przy limicie {money(lim.limit_amount)}. Rozważ podniesienie limitu lub ograniczenie tej kategorii."
                ))
            elif ratio >= Decimal("0.8"):
                recs.append(Recommendation(
                    level="info",
                    title=f"Blisko limitu: {lim.category.name}",
                    message=f"Wykorzystano {ratio*Decimal('100'):.0f}% limitu ({money(spent)} / {money(lim.limit_amount)}). Uważaj do końca miesiąca."
                ))
    else:
        recs.append(Recommendation(
            level="info",
            title="Wskazówka: ustaw limity",
            message="Nie masz ustawionych limitów na kategorie w tym miesiącu. Limity pomagają kontrolować wydatki i generować lepsze rekomendacje."
        ))

    # --- Subskrypcje ---
    subs = Subscription.objects.filter(user=user)
    if subs.exists():
        subs_total = subs.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        if subs_total > 0:
            recs.append(Recommendation(
                level="info",
                title="Subskrypcje",
                message=f"Łącznie płacisz za subskrypcje ok. {money(subs_total)} / miesiąc. Sprawdź, czy wszystkie są potrzebne."
            ))
    # (jeśli nie ma subskrypcji, nie spamujemy komunikatem)

    # Zwracamy jako listę dict (łatwe w template)
    return [{"level": r.level, "title": r.title, "message": r.message} for r in recs]
