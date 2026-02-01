# PRINCIPLES.md

> **Layer 0**: WHY we build

---

## Product Vision

KondateAgent helps home cooks transform "what's in my fridge" into a week of delicious meals. Instead of staring at ingredients wondering what to make, users tell us what they have and we create an optimized meal plan from their favorite recipe creators.

## Problem Statement

Home cooks face several challenges:

1. **Decision fatigue**: "What should I cook tonight?" repeated 7 times a week
2. **Food waste**: Buying ingredients for one recipe, forgetting about them
3. **Recipe discovery**: Finding recipes that use what you already have
4. **Shopping inefficiency**: Buying duplicates or missing key ingredients

## Core Value Proposition

**One input, one week of meals.**

User provides:
- Ingredients they have
- Favorite recipe creators (YouTube/Instagram)

System delivers:
- 7-day meal plan optimized for ingredient usage
- Recipes from creators they trust
- Minimal shopping list for what's missing

## User-Centered Principles

### 1. Minimal Friction
- Voice/text input for ingredients (no typing lists)
- One-tap plan generation
- Natural language refinement ("change Tuesday to something lighter")

### 2. Trust Through Transparency
- Show why each recipe was selected (ingredient overlap, variety)
- Display coverage scores (% of ingredients used)
- Never hide what needs to be purchased

### 3. User Control
- Plans are suggestions, not prescriptions
- Easy to swap individual meals
- Preferences are remembered, not forced

### 4. Mobile-First
- Design for one-handed use while standing in kitchen
- Large touch targets (44x44px minimum)
- Works offline once plan is generated

## Success Metrics

### User Success
- **Plan completion**: % of generated plans where user generates shopping list
- **Swap rate**: Average swaps per plan (lower = better initial suggestions)
- **Return rate**: % of users who generate a second plan within 30 days

### System Success
- **Ingredient coverage**: Average % of user's ingredients used in final plan
- **Shopping list size**: Average items needed beyond what user has
- **Generation time**: Under 10 seconds from ingredients to plan

## Non-Goals

Things we explicitly won't optimize for:

- **Nutritional tracking**: We help with meal planning, not diet management
- **Exact portion calculation**: Recipes vary; users adjust naturally
- **Social features**: No sharing, liking, or community features initially
- **Recipe authoring**: We aggregate existing recipes, don't create them

## Design Philosophy

### Simplicity Over Features
Every new feature must pass: "Does this reduce decision fatigue?"

### Trust The User
- Don't second-guess ingredient quantities
- Don't warn about "unusual" combinations
- Let users make "mistakes" that might be intentional

### Graceful Degradation
- No YouTube creators? Plan works with Instagram only
- LLM fails? Fall back to simple matching
- Offline? Show cached plan and recipes

---

## References

This document guides all feature development. Before building, ask:
- Does this align with our core value proposition?
- Does this reduce friction for the user?
- Is this a feature or scope creep?
