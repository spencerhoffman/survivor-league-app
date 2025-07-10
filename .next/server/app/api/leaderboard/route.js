(()=>{var e={};e.id=35,e.ids=[35],e.modules={846:e=>{"use strict";e.exports=require("next/dist/compiled/next-server/app-page.runtime.prod.js")},4870:e=>{"use strict";e.exports=require("next/dist/compiled/next-server/app-route.runtime.prod.js")},3295:e=>{"use strict";e.exports=require("next/dist/server/app-render/after-task-async-storage.external.js")},9294:e=>{"use strict";e.exports=require("next/dist/server/app-render/work-async-storage.external.js")},3033:e=>{"use strict";e.exports=require("next/dist/server/app-render/work-unit-async-storage.external.js")},9428:e=>{"use strict";e.exports=require("buffer")},5511:e=>{"use strict";e.exports=require("crypto")},4735:e=>{"use strict";e.exports=require("events")},9021:e=>{"use strict";e.exports=require("fs")},1630:e=>{"use strict";e.exports=require("http")},5591:e=>{"use strict";e.exports=require("https")},1645:e=>{"use strict";e.exports=require("net")},1820:e=>{"use strict";e.exports=require("os")},3873:e=>{"use strict";e.exports=require("path")},7910:e=>{"use strict";e.exports=require("stream")},4631:e=>{"use strict";e.exports=require("tls")},9551:e=>{"use strict";e.exports=require("url")},4075:e=>{"use strict";e.exports=require("zlib")},7990:()=>{},636:(e,r,t)=>{"use strict";t.r(r),t.d(r,{patchFetch:()=>v,routeModule:()=>d,serverHooks:()=>x,workAsyncStorage:()=>c,workUnitAsyncStorage:()=>l});var s={};t.r(s),t.d(s,{GET:()=>n});var i=t(2706),u=t(8203),o=t(5994),p=t(9187),a=t(6875);async function n(){try{let e=await (0,a.ll)`
      SELECT 
        p.id as player_id,
        p.entry_name,
        u.username,
        p.status,
        p.weeks_survived,
        p.redemption_visits,
        p.buybacks,
        p.eliminated_week,
        p.financial_contribution,
        u.profile_picture_url
      FROM players p
      JOIN users u ON p.user_id = u.id
      ORDER BY p.weeks_survived DESC, p.redemption_visits ASC, p.buybacks ASC
    `;return p.NextResponse.json(e.rows)}catch(e){return console.error("Get leaderboard error:",e),p.NextResponse.json({error:"Failed to get leaderboard"},{status:500})}}let d=new i.AppRouteRouteModule({definition:{kind:u.RouteKind.APP_ROUTE,page:"/api/leaderboard/route",pathname:"/api/leaderboard",filename:"route",bundlePath:"app/api/leaderboard/route"},resolvedPagePath:"/home/ubuntu/repos/survivor-league-app/app/api/leaderboard/route.ts",nextConfigOutput:"",userland:s}),{workAsyncStorage:c,workUnitAsyncStorage:l,serverHooks:x}=d;function v(){return(0,o.patchFetch)({workAsyncStorage:c,workUnitAsyncStorage:l})}},6487:()=>{},8335:()=>{}};var r=require("../../../webpack-runtime.js");r.C(e);var t=e=>r(r.s=e),s=r.X(0,[638,452,875],()=>t(636));module.exports=s})();