#!/bin/bash
# Related check-app suites against a site dir: run-related.sh <site> <port> <out>
SITE=$1; PORT=$2; OUT=$3; : > $OUT
for n in friendStrip friendMajor homeNoFriends homeFriendsErr friends requests friendsSearch friendsOneList removeFriend chatFriendBack friendProfile myFriendsFail myFriends settings onbReportLast friendPlans signup onbFriendsOnly nativeNoWeb blockedSettingsText inviteToApp darkMode darkLightSame darkSetting darkOnboarding friendsOfFriend friendsOfFriendStates dprPendingPush secSheetLinks; do
  r=$(cd $SITE/app-dev/tests && APP_DIR=$SITE APP_PORT=$PORT timeout 300 node check-app.mjs --only $n --quiet 2>&1 | grep -E "FAIL|passed|failed|Error" | tail -6)
  echo "== $n: $r" >> $OUT
done
