#!/bin/bash
cd "$(dirname "$0")" || exit 1
source ../git.sh
[ -n "$GH_TOKEN" ] || { echo "no GH_TOKEN"; exit 1; }

REPO="github.com/mingjie2026/2608B-TestCode.git"
BRANCH="master"
MSG="${1:-update $(date '+%F %H:%M')}"

[ -d .git ] || {
    git init
    git config user.name "$GH_USER"
    git config user.email "mingjie2026@gmail.com"
}

git checkout -B "$BRANCH"
git add -A
git commit -m "$MSG" || echo "no changes"
git push -f "https://${GH_USER}:${GH_TOKEN}@${REPO}" "$BRANCH"
